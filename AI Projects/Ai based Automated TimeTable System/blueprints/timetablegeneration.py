from flask import Blueprint, render_template, request, url_for, jsonify
from flask_wtf.csrf import CSRFProtect, validate_csrf, CSRFError
import boto3
import pandas as pd
from typing import List, Dict, Any, Optional
import json
import google.generativeai as genai
from aws_credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION_NAME, BUCKET_NAME
from gemini_api import API_KEY
import logging
import re
import random

# Blueprint for timetable routes
timetable_bp = Blueprint('timetable', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure CSRF protection
csrf = CSRFProtect()

# Configure Gemini API
genai.configure(api_key=API_KEY)
gemini_model = "gemini-2.0-flash-thinking-exp"

# AWS S3 client setup
s3 = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

# ------------------------------------------------------------------------
# 1) READ & MERGE EXCEL DATA
# ------------------------------------------------------------------------
def read_excel_data(file_path: str = "timetable_data.xlsx") -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    try:
        faculty_df = pd.read_excel(file_path, sheet_name="Sheet1")
        if faculty_df.empty:
            logging.error("No data found in Sheet1 (Faculty Details)")
            return [], [], []
        
        courses_df = pd.read_excel(file_path, sheet_name="Sheet2")
        if courses_df.empty:
            logging.error("No data found in Sheet2 (Courses)")
            return [], [], []
        
        labs_df = pd.read_excel(file_path, sheet_name="Sheet3")
        if labs_df.empty:
            logging.error("No data found in Sheet3 (Labs)")
            return [], [], []
        
        if all(col in faculty_df.columns for col in ["Course_Code"]) and \
           all(col in courses_df.columns for col in ["Course_Code", "Course_Name"]):
            faculty_df = faculty_df.merge(
                courses_df[['Course_Code', 'Course_Name']], 
                on='Course_Code', 
                how='left', 
                suffixes=('', '_course')
            )
            if 'Subject' not in faculty_df.columns:
                faculty_df['Subject'] = faculty_df['Course_Name']
                logging.info("Created 'Subject' column from Course_Name in faculty data.")
            else:
                faculty_df['Subject'] = faculty_df.apply(
                    lambda row: row['Course_Name'] 
                                if pd.isna(row['Subject']) or str(row['Subject']).strip() == "" 
                                else row['Subject'],
                    axis=1
                )
                logging.info("Filled empty 'Subject' values with Course_Name in faculty data.")
        else:
            logging.warning("Cannot merge courses because required columns are missing in Sheet1/Sheet2.")
        
        no_subject_rows = faculty_df[faculty_df['Subject'].isna() | (faculty_df['Subject'] == '')]
        if not no_subject_rows.empty:
            logging.warning("Some faculty rows have no Subject even after merging with courses:")
            logging.warning(no_subject_rows)
        
        faculty_data = faculty_df.to_dict(orient='records')
        courses_data = courses_df.to_dict(orient='records')
        labs_data    = labs_df.to_dict(orient='records')
        
        logging.info(
            f"Loaded {len(faculty_data)} faculty records, "
            f"{len(courses_data)} course records, {len(labs_data)} lab records"
        )
        return faculty_data, courses_data, labs_data

    except Exception as e:
        logging.error(f"Error reading Excel file: {str(e)}")
        return [], [], []

# ------------------------------------------------------------------------
# 2) S3 UPLOAD & FETCH
# ------------------------------------------------------------------------
def sanitize_faculty_name(faculty_name: Optional[str]) -> str:
    if not faculty_name or not isinstance(faculty_name, str):
        return "unknown_faculty"
    sanitized = re.sub(r'[^\w\s-]', '_', faculty_name).replace(' ', '_').replace(',', '_')
    return sanitized[:128]

def upload_timetable_to_s3(timetable: dict, department: str, type_: str, faculty: Optional[str] = None) -> str:
    if not timetable:
        logging.warning(f"Attempting to upload empty {type_} timetable for {faculty or 'all'} in {department}")
        return ""
    s3_key = f'timetable_generation/{department}/'
    if faculty:
        s3_key += f'{type_}_timetable_{sanitize_faculty_name(faculty)}.json'
    else:
        s3_key += f'{type_}_timetable.json'
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        Body=json.dumps(timetable),
        ContentType='application/json'
    )
    logging.info(f"Timetable stored at s3://{BUCKET_NAME}/{s3_key}")
    return s3_key

def fetch_timetable_from_s3(department: str, type_: str, faculty: Optional[str] = None) -> dict:
    try:
        s3_key = f'timetable_generation/{department}/'
        if faculty:
            s3_key += f'{type_}_timetable_{sanitize_faculty_name(faculty)}.json'
        else:
            s3_key += f'{type_}_timetable.json'
        response = s3.get_object(Bucket=BUCKET_NAME, Key=s3_key)
        timetable = json.loads(response['Body'].read().decode('utf-8'))
        if not timetable:
            logging.warning(f"Empty timetable fetched from s3://{BUCKET_NAME}/{s3_key}")
        return timetable
    except s3.exceptions.NoSuchKey:
        logging.warning(f"Timetable not found at s3://{BUCKET_NAME}/{s3_key}")
        return {}

# ------------------------------------------------------------------------
# 3) ACO ALGORITHM (no lunch)
# ------------------------------------------------------------------------
def run_aco(data: list[dict[str, Any]], constraints: list[str], faculty: Optional[str] = None) -> dict:
    """
    Creates a timetable using a simplified ACO-like approach:
    - If a specific faculty is provided, it builds that faculty's schedule using all matching rows (ignoring department filter).
    - Otherwise, builds schedules for all faculties (using department filtering).
    - Each subject is randomly assigned to an available slot.
    """
    timetable = {}
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    periods = 8

    if faculty:
        # Use case-insensitive matching on Faculty_Name.
        faculty_lower = faculty.strip().lower()
        faculty_data = [d for d in data if d.get('Faculty_Name', '').strip().lower() == faculty_lower]
        if not faculty_data:
            logging.warning(f"No data found for faculty: {faculty}")
            timetable[faculty] = {day: {f'Period{p+1}': '-' for p in range(periods)} for day in days}
            return timetable
        
        timetable[faculty] = {day: {f'Period{p+1}': '-' for p in range(periods)} for day in days}
        subjects = [(d.get('Subject'), d.get('Course_Code')) for d in faculty_data if d.get('Subject')]
        logging.info(f"Subjects for {faculty}: {subjects}")
        for subject, code in subjects:
            assigned = False
            attempts = 0
            max_attempts = 20
            while not assigned and attempts < max_attempts:
                day = random.choice(days)
                period = f'Period{random.randint(1, periods)}'
                if timetable[faculty][day][period] == '-':
                    timetable[faculty][day][period] = f"{subject} ({code})"
                    assigned = True
                attempts += 1
            if not assigned:
                logging.warning(f"Could not assign {subject} ({code}) for {faculty} due to slot unavailability")
    else:
        faculties = {d.get('Faculty_Name') for d in data if d.get('Faculty_Name')}
        for fac in faculties:
            fac_data = [d for d in data if d.get('Faculty_Name') == fac]
            timetable[fac] = {day: {f'Period{p+1}': '-' for p in range(periods)} for day in days}
            subjects = [(d.get('Subject'), d.get('Course_Code')) for d in fac_data if d.get('Subject')]
            logging.info(f"Subjects for {fac}: {subjects}")
            for subject, code in subjects:
                assigned = False
                attempts = 0
                max_attempts = 20
                while not assigned and attempts < max_attempts:
                    day = random.choice(days)
                    period = f'Period{random.randint(1, periods)}'
                    if timetable[fac][day][period] == '-':
                        timetable[fac][day][period] = f"{subject} ({code})"
                        assigned = True
                    attempts += 1
                if not assigned:
                    logging.warning(f"Could not assign {subject} ({code}) for {fac} due to slot unavailability")
    return timetable

# ------------------------------------------------------------------------
# 4) CSP (No Overlaps)
# ------------------------------------------------------------------------
def run_csp(timetable: dict, constraints: list[str]) -> dict:
    for key, schedule in timetable.items():
        for day, periods in schedule.items():
            assigned_periods = [p for p, sub in periods.items() if sub != '-']
            if len(assigned_periods) > len(set(assigned_periods)):
                logging.warning(f"Overlap detected in {key}'s timetable for {day}")
    return timetable

# ------------------------------------------------------------------------
# 5) Graph Coloring (Placeholder)
# ------------------------------------------------------------------------
def run_graph_coloring(timetable: dict, constraints: list[str]) -> dict:
    return timetable

# ------------------------------------------------------------------------
# 6) Genetic Algorithm (Placeholder)
# ------------------------------------------------------------------------
def run_genetic(timetable: dict, constraints: list[str]) -> dict:
    return timetable

# ------------------------------------------------------------------------
# 7) Constraints
# ------------------------------------------------------------------------
def apply_constraints(data: list[dict[str, Any]], timetable_type: str) -> list[str]:
    constraints = {
        "general": ["no overlaps", "room capacity"],
        "lab": ["continuous slots", "equipment availability", "maintenance windows"],
        "course": ["prerequisite sequencing", "inter-departmental clashes"],
    }
    return constraints.get(timetable_type, [])

# ------------------------------------------------------------------------
# 8) GENERATE ALL TIMETABLES
# ------------------------------------------------------------------------
def generate_all_timetables(department: str, faculty: Optional[str] = None) -> tuple[dict, dict, dict, str]:
    faculty_data, courses_data, labs_data = read_excel_data()
    if not any([faculty_data, courses_data, labs_data]):
        logging.error("No data loaded from Excel; cannot generate timetables")
        return {}, {}, {}, "Error: No data loaded"

    # If a faculty is specified, do not filter the faculty_data by department.
    if faculty:
        dept_faculty = [d for d in faculty_data if d.get('Faculty_Name', '').strip().lower() == faculty.strip().lower()]
    else:
        # Otherwise, filter by the department using the "Year" column.
        def filter_by_department(all_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
            if department == "Default Department":
                return all_data
            year_str = department.split()[0].strip().upper()
            filtered = []
            for row in all_data:
                row_year = str(row.get('Year', '')).strip().upper()
                if row_year == year_str:
                    filtered.append(row)
            return filtered
        dept_faculty = filter_by_department(faculty_data)

    # For courses and labs, we still filter by department.
    def filter_by_department(all_data: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if department == "Default Department":
            return all_data
        year_str = department.split()[0].strip().upper()
        filtered = []
        for row in all_data:
            row_year = str(row.get('Year', '')).strip().upper()
            if row_year == year_str:
                filtered.append(row)
        return filtered

    dept_courses = filter_by_department(courses_data)
    dept_labs    = filter_by_department(labs_data)

    faculty_constraints = apply_constraints(dept_faculty, "general") + apply_constraints(dept_faculty, "course")
    faculty_timetable = run_aco(dept_faculty, faculty_constraints, faculty)
    faculty_timetable = run_csp(faculty_timetable, faculty_constraints)
    faculty_timetable = run_graph_coloring(faculty_timetable, faculty_constraints)
    faculty_timetable = run_genetic(faculty_timetable, faculty_constraints)
    if not faculty_timetable:
        logging.warning(f"Faculty timetable empty for {faculty or 'all'} in {department}")

    class_constraints = apply_constraints(dept_courses, "general") + apply_constraints(dept_courses, "course")
    class_timetable = {}
    for course in dept_courses:
        year = course['Year']
        semester = course['Semester']
        class_timetable.setdefault(year, {}).setdefault(semester, {})
        for fac in dept_faculty:
            if course['Course_Code'] == fac.get('Course_Code', ''):
                fac_timetable = faculty_timetable.get(fac['Faculty_Name'], {})
                for day, periods in fac_timetable.items():
                    for period, subject_info in periods.items():
                        if subject_info != '-' and course['Course_Name'] in subject_info:
                            class_timetable[year][semester][f'{day} {period}'] = subject_info

    class_timetable = run_csp(class_timetable, class_constraints)
    if not class_timetable:
        logging.warning(f"Class timetable empty for {department}")

    lab_constraints = apply_constraints(dept_labs, "general") + apply_constraints(dept_labs, "lab")
    lab_timetable = {}
    for lab in dept_labs:
        lab_timetable[lab['Lab_Name']] = {}
        for course in dept_courses:
            if course['Course_Code'] == lab['Course_Code'] and lab['Type'] == 'Lab':
                year = course['Year']
                semester = course['Semester']
                for time_slot, subject_info in class_timetable.get(year, {}).get(semester, {}).items():
                    if course['Course_Name'] in subject_info:
                        lab_timetable[lab['Lab_Name']][time_slot] = subject_info
    lab_timetable = run_csp(lab_timetable, lab_constraints)
    if not lab_timetable:
        logging.warning(f"Lab timetable empty for {department}")

    if faculty:
        upload_timetable_to_s3(faculty_timetable, department, 'faculty', faculty)
    else:
        upload_timetable_to_s3(faculty_timetable, department, 'faculty')
    upload_timetable_to_s3(class_timetable, department, 'class')
    upload_timetable_to_s3(lab_timetable, department, 'lab')

    return faculty_timetable, class_timetable, lab_timetable, "No suggestions"

# ------------------------------------------------------------------------
# 9) FLASK ROUTES
# ------------------------------------------------------------------------
@timetable_bp.route('/faculty-timetable', methods=['GET'])
def faculty_timetable() -> str:
    try:
        faculty_df = pd.read_excel("timetable_data.xlsx", sheet_name="Sheet1")
        if 'Year' in faculty_df.columns:
            valid_years = [str(y).strip() for y in faculty_df['Year'].unique() if pd.notna(y)]
            departments = [f"{y} Year" for y in valid_years]
        else:
            departments = ["Default Department"]
            logging.warning("No 'Year' column found in Sheet1; using default department.")

        faculty_data, _, _ = read_excel_data()
        faculties = sorted(list(set(d.get('Faculty_Name', '') for d in faculty_data if pd.notna(d.get('Faculty_Name', '')))))
        logging.info(f"Retrieved unique faculties: {faculties}")

        user_department = request.args.get('department')
        if user_department:
            department = user_department
        else:
            department = departments[0] if departments else 'Default Department'

        faculty_timetables = {fac: fetch_timetable_from_s3(department, 'faculty', fac) for fac in faculties}
        gemini_suggestion = ""

        return render_template(
            'faculty_timetable.html', 
            departments=departments, 
            faculties=faculties, 
            timetables=faculty_timetables, 
            selected_department=department,
            gemini_suggestion=gemini_suggestion
        )
    except Exception as e:
        logging.error(f"Error in faculty_timetable: {str(e)}")
        return render_template(
            'faculty_timetable.html', 
            departments=["Default Department"], 
            faculties=[], 
            timetables={}, 
            selected_department="Default Department",
            gemini_suggestion=f"Error: {str(e)}"
        )

# ------------------------------------------------------------------------
# CSRF-EXEMPTED Generate Faculty Timetable Route (for testing)
# ------------------------------------------------------------------------
@csrf.exempt
@timetable_bp.route('/generate-faculty-timetable/<path:faculty>', methods=['POST'])
def generate_faculty_timetable(faculty: str) -> tuple[jsonify, int]:
    try:
        faculty = faculty.replace('_', ' ').replace('%20', ' ').replace('%2C', ',')
        logging.info(f"Generating timetable for faculty: {faculty}")

        # CSRF is bypassed here for testing; in production include a valid CSRF token.
        department = request.form.get('department', 'Default Department')
        logging.info(f"Using department: {department}")

        faculty_timetable, _, _, gemini_suggestion = generate_all_timetables(department, faculty)

        return jsonify({
            'faculty_timetable': faculty_timetable,
            'gemini_suggestion': gemini_suggestion,
            'status': 'success'
        }), 200
    except Exception as e:
        logging.error(f"Error generating timetable for {faculty}: {str(e)}")
        return jsonify({'status': 'error', 'message': f'Failed to generate timetable: {str(e)}'}), 400

@csrf.exempt
@timetable_bp.route('/class-timetable')
def class_timetable() -> str:
    faculty_df = pd.read_excel("timetable_data.xlsx", sheet_name="Sheet1")
    if 'Year' in faculty_df.columns:
        valid_years = [str(y).strip() for y in faculty_df['Year'].unique() if pd.notna(y)]
        departments = [f"{y} Year" for y in valid_years]
    else:
        departments = ["Default Department"]

    department = request.args.get('department', departments[0])
    class_timetable = fetch_timetable_from_s3(department, 'class')
    return render_template(
        'class_timetable.html', 
        departments=departments, 
        timetable=class_timetable,
        selected_department=department
    )

@csrf.exempt
@timetable_bp.route('/lab-timetable')
def lab_timetable() -> str:
    faculty_df = pd.read_excel("timetable_data.xlsx", sheet_name="Sheet1")
    if 'Year' in faculty_df.columns:
        valid_years = [str(y).strip() for y in faculty_df['Year'].unique() if pd.notna(y)]
        departments = [f"{y} Year" for y in valid_years]
    else:
        departments = ["Default Department"]

    department = request.args.get('department', departments[0])
    lab_timetable = fetch_timetable_from_s3(department, 'lab')
    return render_template(
        'lab_timetable.html', 
        departments=departments, 
        timetable=lab_timetable,
        selected_department=department
    )

@csrf.exempt
@timetable_bp.route('/')
def index() -> str:
    return render_template('timetablegenerationinfo.html')
