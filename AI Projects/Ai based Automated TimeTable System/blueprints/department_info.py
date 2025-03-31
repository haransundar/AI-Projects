# department_info.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
import boto3
import json
import logging
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect
from flask_wtf.csrf import generate_csrf


csrf = CSRFProtect()

# Load AWS credentials
from aws_credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION_NAME, BUCKET_NAME

# Initialize S3 client
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Blueprint for department info
department_info_bp = Blueprint('department_info', __name__)

# Helper functions for S3 operations
def upload_to_s3(data, folder_name, file_name):
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f'{folder_name}/{file_name}.json',
        Body=json.dumps(data),
        ContentType='application/json'
    )

def download_from_s3(folder_name, file_name):
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=f'{folder_name}/{file_name}.json'
        )
        return json.loads(response['Body'].read().decode('utf-8'))
    except s3_client.exceptions.NoSuchKey:
        logging.warning(f"File not found: {folder_name}/{file_name}.json")
        return {}
    except Exception as e:
        logging.error(f"An error occurred while downloading {folder_name}/{file_name}.json: {str(e)}")
        return {}

def delete_from_s3(folder_name, file_name):
    try:
        s3_client.delete_object(
            Bucket=BUCKET_NAME,
            Key=f'{folder_name}/{file_name}.json'
        )
    except Exception as e:
        logging.error(f"An error occurred while deleting the file {folder_name}/{file_name}.json: {str(e)}")

def list_files_from_s3(folder_name, key):
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=folder_name)
        data_list = []
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                try:
                    file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
                    file_data = json.loads(file_response['Body'].read().decode('utf-8'))
                    if key in file_data and isinstance(file_data[key], list):
                        data_list.extend(file_data[key])
                except (json.JSONDecodeError, KeyError) as e:
                    logging.error(f"Invalid JSON in file {file_key}: {str(e)}")
        return data_list
    except Exception as e:
        logging.error(f"An error occurred while listing files in {folder_name}: {str(e)}")
        return []

# Existing route: Insert Department Info
@department_info_bp.route('/insert_departmentinfo', methods=['GET', 'POST'])
def insert_departmentinfo():
    if request.method == 'POST':
        department_name = request.form['department_name']
        num_courses = int(request.form['num_courses'])
        courses = []
        for i in range(num_courses):
            course_type = request.form[f'course_type_{i}']
            course_name = request.form[f'course_name_{i}']
            courses.append({'type': course_type, 'name': course_name})

        num_faculties = int(request.form['num_faculties'])
        faculties = [request.form[f'faculty_{i}'] for i in range(num_faculties)]

        num_labs = int(request.form['num_labs'])
        labs = []
        for i in range(num_labs):
            lab_name = request.form[f'lab_name_{i}']
            lab_capacity = request.form[f'lab_capacity_{i}']
            labs.append({'name': lab_name, 'capacity': lab_capacity})

        num_classrooms = int(request.form['num_classrooms'])
        classrooms = []
        for i in range(num_classrooms):
            classroom_name = request.form[f'classroom_name_{i}']
            allocated_class = request.form[f'allocated_class_{i}']
            classrooms.append({'name': classroom_name, 'allocated_class': allocated_class})

        department_info = {
            'name': department_name,
            'courses': courses,
            'faculties': faculties,
            'labs': labs,
            'classrooms': classrooms
        }

        # Create a folder named after the department and store the department information
        department_folder = f'department_data/{department_name}'
        upload_to_s3(department_info, department_folder, department_name)

        # Update the list of departments
        departments = download_from_s3('college_data', 'departments')
        if department_name not in departments:
            departments.append(department_name)
            upload_to_s3(departments, 'college_data', 'departments')

        flash('Department information added successfully!', 'success')
        return redirect(url_for('department_info.view_departmentinfo'))

    # Check if we are editing an existing department
    edit_department_name = request.args.get('edit')
    department_info = None
    if edit_department_name:
        department_folder = f'department_data/{edit_department_name}'
        department_info = download_from_s3(department_folder, edit_department_name)

    # Retrieve departments and courses from S3
    departments = list_files_from_s3('college_data', 'departments')
    courses_data = list_files_from_s3('college_data', 'courses')

    # Extract course names from the courses data
    courses = [course['name'] for course in courses_data if 'name' in course]

    # Ensure departments and courses are valid lists
    if not isinstance(departments, list):
        departments = []
    if not isinstance(courses, list):
        courses = []

    return render_template('insert_departmentinfo.html', departments=departments, courses=courses, department_info=department_info)

# Existing route: View Department Info
@department_info_bp.route('/view_departmentinfo', methods=['GET'])
def view_departmentinfo():
    # Retrieve the list of departments from S3
    departments = list_files_from_s3('college_data', 'departments')

    # Ensure departments is a list and contains only valid strings
    if not isinstance(departments, list):
        departments = []
    departments = [dept for dept in departments if isinstance(dept, str)]

    # Initialize department_data dictionary
    department_data = {}

    # Iterate over each department and retrieve its information
    for department_name in departments:
        department_folder = f'department_data/{department_name}'
        department_info = download_from_s3(department_folder, department_name)

        # Ensure department_info is a dictionary
        if not isinstance(department_info, dict):
            department_info = {}

        department_data[department_name] = department_info

    return render_template('view_departmentinfo.html', department_data=department_data)

# Route to provide CSRF token to frontend (optional, if needed)
@department_info_bp.route('/get_csrf_token', methods=['GET'])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({'csrf_token': token})

@department_info_bp.route('/delete_departmentinfo', methods=['POST'])
@csrf.exempt
def delete_departmentinfo():
    # The CSRF token will be validated automatically by Flask-WTF
    try:
        data = request.get_json()
        if not data:
            flash("No data provided in the request.", "error")
            return jsonify({'success': False, 'message': 'No data provided'}), 400
    except Exception as e:
        logging.error(f"Failed to parse JSON request: {str(e)}")
        flash("Invalid request format.", "error")
        return jsonify({'success': False, 'message': 'Invalid request format'}), 400

    department_name = data.get('department_name')
    if not department_name or not isinstance(department_name, str) or department_name.strip() == "":
        logging.error("Invalid or missing department name in request.")
        flash("Invalid or missing department name.", "error")
        return jsonify({'success': False, 'message': 'Invalid department name'}), 400

    department_folder = f'department_data/{department_name}'

    try:
        delete_from_s3(department_folder, department_name)
        logging.info(f"Department {department_name} deleted successfully from S3.")

        departments = download_from_s3('college_data', 'departments')
        if not isinstance(departments, list):
            logging.warning(f"Departments data is not a list: {departments}. Initializing as empty list.")
            departments = []

        if department_name in departments:
            departments.remove(department_name)
            upload_to_s3(departments, 'college_data', 'departments')
            logging.info(f"Updated department list: {departments}")

        flash(f"Department {department_name} deleted successfully!", "success")
        return jsonify({'success': True, 'message': f'Department {department_name} deleted successfully'})

    except Exception as e:
        logging.error(f"Error deleting department {department_name}: {str(e)}")
        flash(f"Failed to delete department {department_name}: {str(e)}", "error")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500
    
# Routes
@department_info_bp.route('/edit_departmentinfo/<department_name>', methods=['GET'])
def edit_departmentinfo(department_name):
    department_folder = f'department_data/{department_name}'
    department_info = download_from_s3(department_folder, department_name)

    # Ensure department_info is a dictionary
    if not isinstance(department_info, dict):
        flash('Department information not found!', 'error')
        return redirect(url_for('department_info.view_departmentinfo'))

    # Ensure the dictionary has the expected structure
    expected_keys = ['name', 'courses', 'faculties', 'labs', 'classrooms']
    if not all(key in department_info for key in expected_keys):
        flash('Department information is incomplete!', 'error')
        return redirect(url_for('department_info.view_departmentinfo'))

    return render_template('edit_departmentinfo.html', department_info=department_info)

@department_info_bp.route('/update_departmentinfo', methods=['POST'])
def update_departmentinfo():
    try:
        # Verify CSRF token
        csrf.protect()

        department_name = request.form['department_name']
        existing_department_info = download_from_s3(f'department_data/{department_name}', department_name)

        # Ensure existing_department_info is a dictionary
        if not isinstance(existing_department_info, dict):
            existing_department_info = {
                'name': department_name,
                'courses': [],
                'faculties': [],
                'labs': [],
                'classrooms': []
            }

        # Update courses
        num_courses = int(request.form.get('num_courses', 0))
        courses = []
        for i in range(num_courses):
            course_type = request.form.get(f'course_type_{i}', '')
            course_name = request.form.get(f'course_name_{i}', '')
            if course_type and course_name:
                courses.append({'type': course_type, 'name': course_name})

        # Update faculties
        num_faculties = int(request.form.get('num_faculties', 0))
        faculties = []
        for i in range(num_faculties):
            faculty_name = request.form.get(f'faculty_{i}', '')
            if faculty_name:
                faculties.append(faculty_name)

        # Update labs
        num_labs = int(request.form.get('num_labs', 0))
        labs = []
        for i in range(num_labs):
            lab_name = request.form.get(f'lab_name_{i}', '')
            lab_capacity = request.form.get(f'lab_capacity_{i}', '')
            if lab_name and lab_capacity:
                labs.append({'name': lab_name, 'capacity': lab_capacity})

        # Update classrooms
        num_classrooms = int(request.form.get('num_classrooms', 0))
        classrooms = []
        for i in range(num_classrooms):
            classroom_name = request.form.get(f'classroom_name_{i}', '')
            allocated_class = request.form.get(f'allocated_class_{i}', '')
            if classroom_name and allocated_class:
                classrooms.append({'name': classroom_name, 'allocated_class': allocated_class})

        # Merge updated data
        department_info = {
            'name': department_name,
            'courses': courses,
            'faculties': faculties,
            'labs': labs,
            'classrooms': classrooms
        }

        # Log the updated department info
        logging.info(f"Updated department info: {department_info}")

        # Upload updated department information to S3
        department_folder = f'department_data/{department_name}'
        upload_to_s3(department_info, department_folder, department_name)

        flash('Department information updated successfully!', 'success')
        return redirect(url_for('department_info.view_departmentinfo'))
    except CSRFError as e:
        flash('CSRF token is missing or invalid!', 'error')
        return redirect(url_for('department_info.edit_departmentinfo', department_name=request.form.get('department_name', '')))
    except ValueError as e:
        flash(f'Invalid form data: {e}', 'error')
        return redirect(url_for('department_info.edit_departmentinfo', department_name=request.form.get('department_name', '')))
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(url_for('department_info.edit_departmentinfo', department_name=request.form.get('department_name', '')))
