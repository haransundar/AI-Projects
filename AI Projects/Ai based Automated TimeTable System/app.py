from flask import Flask, redirect, url_for, render_template
from flask_wtf.csrf import CSRFProtect
from blueprints.college_info_bp import college_info_bp
from blueprints.department_info import department_info_bp
from blueprints.timetablegeneration import timetable_bp,csrf


# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Replace with a secure secret key
csrf = CSRFProtect(app)  # Enable CSRF protection
csrf.init_app(app)

# Register blueprints
app.register_blueprint(college_info_bp, url_prefix='/college')
app.register_blueprint(department_info_bp, url_prefix='/department')
app.register_blueprint(timetable_bp)

# Default route
@app.route('/')
def home():
    return redirect(url_for('college_info_bp.insert_info'))

# College-related routes (if not handled in the blueprint)
@app.route('/college/insert', methods=['GET', 'POST'])
def insert_college_info():
    # Your view logic here
    return render_template('insert_info.html')

@app.route('/college/view', methods=['GET'])
def view_college_info():
    # Your view logic here
    return render_template('view_info.html')

if __name__ == '__main__':
    app.run(debug=True)