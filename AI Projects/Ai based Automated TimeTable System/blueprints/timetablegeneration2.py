from flask import Blueprint, render_template, request
import boto3
from aws_credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, REGION_NAME, BUCKET_NAME

timetable_bp = Blueprint('timetable', __name__)

s3 = boto3.client('s3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=REGION_NAME
)

def list_files_from_s3(bucket, prefix):
    response = s3.list_objects_v2(Bucket=bucket, Prefix=prefix)
    return [obj['Key'].split('/')[-1] for obj in response.get('Contents', [])]

@timetable_bp.route('/table-generation')
def table_generation():
    departments = list_files_from_s3(BUCKET_NAME, 'college_data/departments')
    return render_template('timetablegeneration.html', departments=departments, faculties=[])

@timetable_bp.route('/generate-timetable', methods=['POST'])
def generate_timetable():
    department = request.form['department']
    # Generate timetable logic here
    return render_template('timetablegeneration.html', departments=[department], faculties=[])