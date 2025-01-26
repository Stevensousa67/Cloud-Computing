from flask import Flask, get_flashed_messages, request, render_template, flash, redirect, url_for
from db import get, create
import secrets

app = Flask(__name__)

# Set a secret key for session management
app.secret_key = secrets.token_hex(16)  # Generates a secure random string

@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/get', methods=['GET'])
def get_students():
    return get()

@app.route('/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        student = {"id": request.form.get('id'), "name": request.form.get('name')}
        try:
            create(student)  # Attempt to add the student
            flash("Student added successfully!", "success")
        except Exception as e:
            flash("Failed to add student: " + str(e), "danger")
        return redirect(url_for('add_student'))  # Redirect to the same route to clear the form
    
    # For GET requests, retrieve flashed messages
    flash_messages = get_flashed_messages(with_categories=True)
    return render_template('add_student_form.html', flash_messages=flash_messages)

if __name__ == '__main__':
    app.run(debug=True)