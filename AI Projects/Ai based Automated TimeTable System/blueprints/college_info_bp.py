from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import boto3
import json
from aws_credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION_NAME, BUCKET_NAME
import logging

logging.basicConfig(level=logging.DEBUG)

# Initialize Blueprint
college_info_bp = Blueprint('college_info_bp', __name__, template_folder='../templates')

# AWS S3 Configuration
s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

# Folder (Prefix) for storing data in S3
S3_FOLDER = "college_data/"

@college_info_bp.route('/insert', methods=['GET', 'POST'])
def insert_info():
    if request.method == 'POST':
        try:
            # Extract form data
            courses = []
            for i in range(len(request.form.getlist('course[]')) // 2):
                branch = request.form.getlist('course[]')[i * 2]
                name = request.form.getlist('course[]')[i * 2 + 1]
                courses.append({"name": name, "branch": branch})

            departments = request.form.getlist('department[]')
            periods = request.form.getlist('period[]')

            # Generate a unique key for the file (e.g., timestamp-based)
            import time
            file_key = f"{S3_FOLDER}info_{int(time.time())}.json"

            # Save to S3
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_key,
                Body=json.dumps({
                    "courses": courses,
                    "departments": departments,
                    "periods": periods
                })
            )
            return redirect(url_for('college_info_bp.view_info'))
        except Exception as e:
            return f"An error occurred: {str(e)}", 500
    return render_template('insert_info.html')

@college_info_bp.route('/view', methods=['GET'])
def view_info():
    try:
        # List all objects in the S3 folder
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_FOLDER)

        # Retrieve all JSON files from the folder
        data_list = []
        if 'Contents' in response:
            for obj in response['Contents']:
                file_key = obj['Key']
                file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
                file_data = json.loads(file_response['Body'].read().decode('utf-8'))
                
                # Ensure file_data is a dictionary
                if not isinstance(file_data, dict):
                    continue  # Skip this file if it's not a dictionary
                
                data_list.append(file_data)

        # Combine all data into a single dictionary
        combined_data = {
            "courses": [],
            "departments": [],
            "periods": []
        }
        
        for data in data_list:
            combined_data["courses"].extend(data.get("courses", []))
            combined_data["departments"].extend(data.get("departments", []))
            combined_data["periods"].extend(data.get("periods", []))

        return render_template('view_info.html', data=combined_data)
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@college_info_bp.route('/delete', methods=['POST'])
def delete_info():
    try:
        item_type = request.form.get('type')
        item_value = request.form.get('value')
        logging.debug(f"Deleting {item_type}: {item_value}")

        # Fetch all data from S3
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_FOLDER)
        if 'Contents' not in response:
            logging.error("No data found in S3")
            return jsonify({"status": "error", "message": "No data found in S3"}), 404

        # Process each file
        for obj in response['Contents']:
            file_key = obj['Key']
            logging.debug(f"Processing file: {file_key}")
            file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
            file_data = json.loads(file_response['Body'].read().decode('utf-8'))

            # Handle course deletion
            if item_type == 'course':
                initial_count = len(file_data.get("courses", []))
                file_data["courses"] = [
                    course for course in file_data.get("courses", [])
                    if course.get("name") != item_value
                ]
                final_count = len(file_data["courses"])
                logging.debug(f"Deleted {initial_count - final_count} courses from {file_key}")

            # Handle department deletion
            elif item_type == 'department':
                initial_count = len(file_data.get("departments", []))
                file_data["departments"] = [
                    dept for dept in file_data.get("departments", [])
                    if dept != item_value
                ]
                final_count = len(file_data["departments"])
                logging.debug(f"Deleted {initial_count - final_count} departments from {file_key}")

            # Update the file in S3
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=file_key,
                Body=json.dumps(file_data)
            )

        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error in /delete: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

@college_info_bp.route('/add', methods=['POST'])
def add_info():
    try:
        item_type = request.form.get('type')  # 'course' or 'department'
        item_value = request.form.get('value')

        # Fetch the latest file from S3
        response = s3_client.list_objects_v2(Bucket=BUCKET_NAME, Prefix=S3_FOLDER)
        latest_file_key = None
        if 'Contents' in response:
            latest_file_key = max(response['Contents'], key=lambda obj: obj['LastModified'])['Key']

        if latest_file_key:
            # Fetch the latest file's data
            file_response = s3_client.get_object(Bucket=BUCKET_NAME, Key=latest_file_key)
            file_data = json.loads(file_response['Body'].read().decode('utf-8'))

            # Add the new item
            if item_type == 'course':
                file_data["courses"].append(item_value)
            elif item_type == 'department':
                file_data["departments"].append(item_value)

            # Update the file in S3
            s3_client.put_object(
                Bucket=BUCKET_NAME,
                Key=latest_file_key,
                Body=json.dumps(file_data)
            )

        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500