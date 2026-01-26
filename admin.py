from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from functools import wraps
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from utils import email_create
import pandas as pd
import pyotp
from utils import email_create, tgt_name, name_parts

app = Flask(__name__)
app.secret_key = '***'

MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'sql123',
    'database': 'student_events'
}

ph = PasswordHasher()

def get_db_connection():
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        raise

def get_db_cursor(connection):
    return connection.cursor(dictionary=True)

def get_next_student_id():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT MAX(student_id) AS max FROM students")
        result = cursor.fetchone()
        return (result['max'] or 0) + 1
    finally:
        cursor.close()
        connection.close()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        connection = get_db_connection()
        cursor = get_db_cursor(connection)
        try:
            cursor.execute("SELECT * FROM admin WHERE email = %s", (email,))
            admin = cursor.fetchone()

            if admin:
                try:
                    ph.verify(admin['password'], password)
                    user_secret = None

                    if not user_secret:
                        user_secret = pyotp.random_base32()
                        cursor.execute("UPDATE admin SET otp_secret = %s WHERE id = %s", (user_secret, admin['id']))
                        connection.commit()

                    session['temp_admin_id'] = admin['id']
                    session['temp_admin_name'] = admin['name']
                    session['temp_admin_secret'] = user_secret
                    session['temp_admin_email'] = email
                    
                    totp = pyotp.TOTP(user_secret.upper(), interval=600)
                    current_code = totp.now()
                                        
                    print(f"Login code for : {current_code}")
                    flash(f'{current_code}', 'info')
                    
                    return redirect(url_for('verify_otp'))
                
                except VerifyMismatchError:
                    flash('Invalid email or password', 'error')

            else:
                flash('Invalid email or password', 'error')
                
        finally:
            cursor.close()
            connection.close()
            
    return render_template('admin_login.html')

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if 'temp_admin_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        user_code = request.form.get('otp_code')
        user_secret = session.get('temp_admin_secret')
        
        totp = pyotp.TOTP(user_secret, interval=600)
        
        if totp.verify(user_code):
            session['user_id'] = session.pop('temp_admin_id')
            session['name'] = session.pop('temp_admin_name')
            session.pop('temp_admin_secret')
            session['role'] = 'admin'
            session['email'] = session.pop('temp_admin_email')
            
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid or expired code.', 'error')

    return render_template('verify_otp.html')


@app.route('/add_student', methods=['GET','POST'])
def add_student():
    if request.method == 'POST':
        connection = get_db_connection()
        cursor = get_db_cursor(connection)

        first_name = request.form.get('first-name')
        middle_name = request.form.get('middle-name')
        last_name = request.form.get('last-name')
        name = tgt_name(first_name, middle_name, last_name)
        grade = request.form.get('grade')
        section = request.form.get('section')
        gender = request.form.get('gender')
        date_of_birth = request.form.get('birthdate')
        position = request.form.get('position', None)
        position = position if position in ['prefect', 'house_leader', 'event_coordinator', 'club_leader'] else None
        club = request.form.get('club', None)

        try:
            cursor.execute("SELECT student_id FROM students ORDER BY student_id DESC LIMIT 1")
            last_id = cursor.fetchone()
            student_id = last_id['student_id'] + 1 if last_id else 1
            email = email_create(name, student_id)

            cursor.execute("""
                INSERT INTO students (name, grade, section, birthdate, gender, email, club_id, position)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (name, grade, section, date_of_birth, gender, email, club, position))
            connection.commit()

            flash('Student added successfully', 'success')
            return redirect(url_for('add_student'))
        
        finally:
            cursor.close()
            connection.close()

    return render_template('add_student.html')

@app.route('/admindashboard')
@login_required
def admin_dashboard():
    return render_template('admindashboard.html')

@app.route('/manage_students', methods=['GET','POST'])
@login_required
def manage_students():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    try:
        cursor.execute("""
            SELECT s.student_id, s.name, s.grade, s.section, s.email
            FROM students s
            ORDER BY s.student_id ASC
        """)
        students = cursor.fetchall()
        return render_template('manage_student.html', students=students)
    finally:
        cursor.close()
        connection.close()

@app.route('/manage_students/remove_student/<student_id>', methods=['POST'])
@login_required
def remove_student(student_id):
    if request.method == 'POST':
        connection = get_db_connection()
        cursor = get_db_cursor(connection)

        try:
            cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
            cursor.execute("DELETE FROM users WHERE student_id = %s", (student_id,))
            cursor.execute("DELETE FROM registrations WHERE student_id = %s", (student_id,))
            connection.commit()

            flash('Student removed successfully', 'success')
        
        except Error as e:
            connection.rollback()
            flash(f'Error removing student: {e}', 'error')
            return redirect(url_for('remove_student'))
        
        finally:
            cursor.close()
            connection.close()
        return redirect(url_for('manage_students'))
    
    return redirect(url_for('manage_students'))

@app.route('/new_academic_session', methods=['GET', 'POST'])
@login_required
def new_academic_session():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)

    cursor.execute("SELECT student_id FROM students WHERE grade = 12")
    GR12 = cursor.fetchall()

    try:
        for student in GR12:
            cursor.execute("DELETE FROM users WHERE student_id = %s", (student['student_id'],))
            cursor.execute("DELETE FROM registrations WHERE student_id = %s", (student['student_id'],))
            cursor.execute("DELETE FROM students WHERE student_id = %s", (student['student_id'],))

    except Error as e:
        connection.rollback()
        flash(f'Error processing grade 12 students: {e}', 'error')
        return redirect(url_for('admin_dashboard'))
    
    try:
        cursor.execute("UPDATE students SET grade = grade + 1 WHERE grade < 12")
        connection.commit()
        flash('Academic session updated successfully', 'success')
    
    except Error as e:
        connection.rollback()
        flash(f'Error updating academic session: {e}', 'error')
        return redirect(url_for('admin_dashboard'))
    
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
@login_required
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/manage_student/update_student/<student_id>', methods=['GET','POST'])
@login_required
def update_student(student_id):
    if request.method == 'POST':
        connection = get_db_connection()
        cursor = get_db_cursor(connection)

        try:
            cursor.execute("SELECT NAME FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            first, middle, last = name_parts(student['NAME'])
        except Error as e:
            flash(f'Error fetching student data: {e}', 'error')
            return redirect(url_for('manage_students'))

        first_name = request.form.get('first-name', '')
        first_name = first_name if first_name else first
        middle_name = request.form.get('middle-name', None)
        middle_name = middle_name if middle_name else middle
        last_name = request.form.get('last-name', '')
        last_name = last_name if last_name else last
        name = tgt_name(first_name, middle_name, last_name)
        grade = request.form.get('grade', None)
        section = request.form.get('section', None)
        gender = request.form.get('gender', None)
        date_of_birth = request.form.get('birthdate', None)
        position = request.form.get('position', None)
        position = position if position in ['prefect', 'house_leader', 'event_coordinator', 'club_leader'] else None
        club_id = request.form.get('club', None)

        try:

            if name:
                cursor.execute("UPDATE students SET name=%s WHERE student_id=%s", (name, student_id)) 
            if grade:
                cursor.execute("UPDATE students SET grade=%s WHERE student_id=%s", (grade, student_id))
            if section:
                cursor.execute("UPDATE students SET section=%s WHERE student_id=%s", (section, student_id))
            if gender:
                cursor.execute("UPDATE students SET gender=%s WHERE student_id=%s", (gender, student_id))
            if date_of_birth:
                cursor.execute("UPDATE students SET birthdate=%s WHERE student_id=%s", (date_of_birth, student_id))
            if position:
                cursor.execute("UPDATE students SET position=%s WHERE student_id=%s", (position, student_id))
            if club_id:
                cursor.execute("UPDATE students SET club=%s WHERE student_id=%s", (club_id, student_id))

            connection.commit()
            flash('Student updated successfully', 'success')
            return render_template('update_student.html', student_id = student_id)

        except Error as e:
            connection.rollback()
            flash(f'Error updating student: {e}', 'error')
            return redirect(url_for('manage_students'))

        finally:
            cursor.close()
            connection.close()

    return redirect(url_for('manage_students'))


@app.route('/update_students_xlsx', methods=['GET','POST']) #WORK IN PROGRESS
@login_required
def update_students_xlsx():
    if request.method == 'POST':
        file = request.files['file']
        if not file:
            flash('No file selected', 'error')
            return redirect(url_for('manage_students'))

        try:
            df = pd.read_excel(file)
        except Exception as e:
            flash(f'Error reading Excel file: {e}', 'error')
            return redirect(url_for('manage_students'))

        connection = get_db_connection()
        cursor = get_db_cursor(connection)

        try:
            cursor.execute("SELECT student_id FROM students")
            existing_students = cursor.fetchall()
            existing_student_ids = {student['student_id'] for student in existing_students}

            for index, row in df.iterrows():
                if row['student_id'] in existing_student_ids:
                    cursor.execute("""
                        UPDATE students
                        SET name=%s, grade=%s, section=%s, birthdate=%s, gender=%s, club=%s, position=%s
                        WHERE student_id=%s""",
                        (row['name'], row['grade'], row['section'], row['birthdate'], row['gender'], row['club'], row['position'], row['student_id'])
                    )
                else:
                    email = email_create(row['name'], row['student_id'])
                    cursor.execute("""
                        INSERT INTO students (student_id, name, grade, section, birthdate, gender, email, club, position)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (row['student_id'], row['name'], row['grade'], row['section'], row['birthdate'], row['gender'], email, row['club'], row['position'])
                    )
            connection.commit()
            flash('Students updated successfully', 'success')
            return redirect(url_for('manage_students'))
        except Error as e:
            connection.rollback()
            flash(f'Error updating students: {e}', 'error')
            return redirect(url_for('manage_students'))
        finally:
            cursor.close()
            connection.close()

    return render_template('update_students_xlsx.html')
    
@app.route('/search_students')
@login_required
def search_students():
    query = request.args.get('q', '')
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        position = session.get('position', 'none')
        user_house = session.get('house')
        
        if position == 'house_leader' and user_house:
            if query:
                cursor.execute("""
                    SELECT s.student_id, s.name, s.grade, s.section, u.email
                    FROM students s
                    JOIN users u ON s.student_id = u.student_id
                    WHERE s.house = %s AND (s.name LIKE %s OR u.email LIKE %s OR s.student_id LIKE %s)
                    LIMIT 20
                """,
                (user_house, f'%{query}%', f'%{query}%', f'%{query}%'))
            else:
                cursor.execute("""
                    SELECT s.student_id, s.name, s.grade, s.section, u.email
                    FROM students s
                    JOIN users u ON s.student_id = u.student_id
                    WHERE s.house = %s
                    LIMIT 20
                """,
                (user_house,))
        else:
            if query:
                cursor.execute("""
                    SELECT s.student_id, s.name, s.grade, s.section, u.email
                    FROM students s
                    JOIN users u ON s.student_id = u.student_id
                    WHERE s.name LIKE %s OR u.email LIKE %s OR s.student_id LIKE %s
                    LIMIT 20
                """,
                (f'%{query}%', f'%{query}%', f'%{query}%'))
            else:
                cursor.execute("""
                    SELECT s.student_id, s.name, s.grade, s.section, u.email
                    FROM students s
                    JOIN users u ON s.student_id = u.student_id
                    LIMIT 20
                """)
        
        students = cursor.fetchall()
        return jsonify([dict(s) for s in students])
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True, port=8080)