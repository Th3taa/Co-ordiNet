from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import mysql.connector
from mysql.connector import Error
from functools import wraps
from datetime import datetime
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from utils import Event_ID_IH, Event_ID_IS


app = Flask(__name__)
app.secret_key = '***'


MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '***',
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


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('login'))
            user_role = session.get('position', 'none')
            if user_role not in roles and 'prefect' not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def grades_to_hex(grades):
    hex_map = {i: hex(i)[-1].upper() for i in range(1, 13)}
    return ''.join([hex_map.get(g, '0') for g in sorted(grades)])

def hex_to_grades(hex_str):
    hex_to_num = {hex(i)[-1].upper(): i for i in range(1, 13)}
    return [hex_to_num.get(h, 0) for h in hex_str if h in hex_to_num]



@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        connection = get_db_connection()
        cursor = get_db_cursor(connection)
        try:
            # Join Users with Students to get all necessary information
            cursor.execute("""
                SELECT u.student_id, u.email, u.password, u.position,
                       s.name, s.grade, s.gender, s.house, s.club_id
                FROM users u
                JOIN students s ON u.student_id = s.student_id
                WHERE u.email = %s
            """, (email,))
            user = cursor.fetchone()
            
            if user:
                try:
                    ph.verify(user['password'], password)
                    session['user_id'] = user['student_id']
                    session['name'] = user['name']
                    session['position'] = user['position'] if user['position'] else 'none'
                    session['grade'] = user['grade']
                    session['gender'] = user['gender']
                    session['house'] = user['house']
                    session['club_id'] = user['club_id']
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))
                except VerifyMismatchError:
                    flash('Invalid email or password', 'error')
            else:
                flash('Invalid email or password', 'error')

        finally:
            cursor.close()
            connection.close()

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        grade = int(request.form.get('grade'))
        section = request.form.get('section')
        birthdate = request.form.get('birthdate')
        gender = request.form.get('gender')
        email = request.form.get('email')
        password = request.form.get('password')
        
        hashed_password = ph.hash(password)
        
        connection = get_db_connection()
        cursor = get_db_cursor(connection)
        try:
            cursor.execute("""
                SELECT student_id, position FROM students 
                WHERE name = %s AND grade = %s AND section = %s AND birthdate = %s AND gender = %s AND email = %s
            """,
            (name, grade, section, birthdate, gender, email))
            student = cursor.fetchone()
            
            if not student:
                flash('Registration failed: Student information not found in records. Please verify your details or contact administration.', 'error')
                return redirect(url_for('register'))
            
            cursor.execute("SELECT * FROM users WHERE student_id = %s OR email = %s", 
                       (student['student_id'], email))
            existing_user = cursor.fetchone()
            
            if existing_user:
                flash('An account with this email or student ID already exists. Please login instead.', 'error')
                return redirect(url_for('login'))
            
            cursor.execute("""
                INSERT INTO users (student_id, email, password, position)
                VALUES (%s, %s, %s, %s)
            """, 
            (student['student_id'], email, hashed_password, student['position']))
            connection.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        
        except Exception as e:
            connection.rollback()
            flash(f'Registration failed: {str(e)}', 'error')

        finally:
            cursor.close()
            connection.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("""
            SELECT e.*, 
                   COUNT(r.student_id) as registered_count,
                   CASE WHEN r2.student_id IS NOT NULL THEN 1 ELSE 0 END as is_registered
            FROM events e
            LEFT JOIN registrations r ON e.event_id = r.event_id
            LEFT JOIN registrations r2 ON e.event_id = r2.event_id AND r2.student_id = %s
            GROUP BY e.event_id
            ORDER BY e.created_at DESC
        """,
        (session['user_id'],))
        events = cursor.fetchall()
        
        cursor.execute("SELECT event_id FROM registrations WHERE student_id = %s", (session['user_id'],))
        registered_events = {row['event_id'] for row in cursor.fetchall()}
        
    finally:
        cursor.close()
        connection.close()
    
    return render_template('dashboard.html', events=events, registered_events=registered_events)

@app.route('/event/register/<event_id>', methods=['POST'])
@login_required
def register_event(event_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        current_date = datetime.now().date()
        cursor.execute("SELECT * FROM registrations WHERE student_id = %s AND event_id = %s",
                    (session['user_id'], event_id))
        if cursor.fetchone():
            flash('You are already registered for this event', 'info')
            return redirect(url_for('dashboard'))
        
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()

        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('dashboard'))
        
        if event['grades_eligible']:
            eligible_grades = [int(g) for g in event['grades_eligible'].split(',') if g.strip()]
            if session['grade'] not in eligible_grades:
                flash('You are not eligible for this event based on your grade', 'error')
                return redirect(url_for('dashboard'))

        if event['ages_eligible']:
            eligible_ages = [int(a) for a in event['ages_eligible'].split(',') if a.strip()]
            birthdate = datetime.strptime(session.get('birthdate', '2000-01-01'), '%Y-%m-%d').date()
            age = current_date - birthdate
            age_years = age.days // 365
            if age_years not in eligible_ages:
                flash('You are not eligible for this event based on your age', 'error')
                return redirect(url_for('dashboard'))
        
        if event['gender'] and event['gender'] != 'A':
            if event['gender'] == 'G' and session['gender'] != 'G':
                flash('This event is only for girls', 'error')
                return redirect(url_for('dashboard'))
            if event['gender'] == 'B' and session['gender'] != 'B':
                flash('This event is only for boys', 'error')
                return redirect(url_for('dashboard'))
            
        if current_date > event['last_registration_date']:
            flash('The registration deadline for this event has passed', 'error')
            return redirect(url_for('dashboard'))
        
        cursor.execute("INSERT INTO registrations (student_id, event_id) VALUES (%s, %s)",
                    (session['user_id'], event_id))
        connection.commit()
        flash('Successfully registered for the event!', 'success')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/event/unregister/<event_id>', methods=['POST'])
@login_required
def unregister_event(event_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("DELETE FROM registrations WHERE student_id = %s AND event_id = %s",
                    (session['user_id'], event_id))
        connection.commit()
        flash('Successfully unregistered from the event', 'success')
        return redirect(url_for('dashboard'))
    finally:
        cursor.close()
        connection.close()

@app.route('/event/create', methods=['GET', 'POST'])
@login_required
def create_event():
    position = session.get('position', 'none')
    student_id = session.get('user_id')
    
    if position not in ['event_coordinator', 'club_leader', 'prefect']:
        flash('You do not have permission to create events', 'error')
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        event_name = request.form.get('event_name')
        event_type = request.form.get('event_type')
        grades_eligible = request.form.get('grades_eligible', '')
        ages_eligible = request.form.get('ages_eligible', '')
        gender = request.form.get('gender', 'A')
        last_registration_date = request.form.get('last_registration_date', '')
        event_date = request.form.get('event_date', '')
        main_event = request.form.get('main_event', '')
        main_event_new = request.form.get('main_event_new', '').strip()
        created_by = student_id
        club_no = request.form.get('club_no', '').strip()
        event_summary = request.form.get('event_summary', '')
        
        if main_event_new:
            main_event = main_event_new
        
        connection = get_db_connection()
        cursor = get_db_cursor(connection)
        try:
            club_id = None
            if event_type == 'interhouse':
                if position not in ['club_leader', 'prefect']:
                    flash('Only Club Leaders and Prefects can create interhouse events', 'error')
                    return redirect(url_for('create_event'))
                
                if not club_no:
                    flash('Club number is required for interhouse events', 'error')
                    return redirect(url_for('create_event'))
                
                if position == 'club_leader':
                    club_id = session.get('club_id')
                    if not club_id:
                        flash('You must be assigned to a club to create interhouse events', 'error')
                        return redirect(url_for('create_event'))
                
                if grades_eligible:
                    grade_list = [int(g.strip()) for g in grades_eligible.split(',')]
                    grade_set = set(grade_list)
                    event_id = Event_ID_IH(int(club_no), grade_set, gender)
                else:
                    event_id = Event_ID_IH(int(club_no), set(range(1, 13)), gender)
            
            else:
                cursor.execute("SELECT COUNT(*) as count FROM events WHERE event_id LIKE 'IS%'")
                count = cursor.fetchone()['count']
                next_no = count + 1
                
                if position == 'club_leader':
                    club_id = session.get('club_id')
                    if not club_id:
                        flash('You must be assigned to a club to create interschool events', 'error')
                        return redirect(url_for('create_event'))
                
                if grades_eligible:
                    grade_list = [int(g.strip()) for g in grades_eligible.split(',')]
                else:
                    grade_list = list(range(1, 13))
                
                event_id = Event_ID_IS(next_no, grade_list, gender, main_event if main_event else None)
            
            cursor.execute("""
                INSERT INTO events (event_id, event_name, event_type, grades_eligible, ages_eligible, gender, last_registration_date, event_date, main_event, club_id, created_by, event_summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (event_id, event_name, event_type, grades_eligible, ages_eligible, gender, last_registration_date, event_date, main_event if main_event else None, club_id, created_by, event_summary))

            connection.commit()
            flash(f'Event created successfully! Event ID: {event_id}', 'success')
            return redirect(url_for('dashboard'))
        
        except Exception as e:
            connection.rollback()
            flash(f'Error creating event: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT DISTINCT main_event FROM events WHERE main_event IS NOT NULL")
        main_events = [row['main_event'] for row in cursor.fetchall()]
    finally:
        cursor.close()
        connection.close()
    
    return render_template('create_event.html', main_events=main_events)

@app.route('/event/manage/<event_id>')
@login_required
def manage_event(event_id):
    position = session.get('position', 'none')
    user_id = session.get('user_id')
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('dashboard'))
        
        can_manage = False
        user_house = session.get('house')
        user_club_id = session.get('club_id')
        
        if position == 'prefect':
            can_manage = True
        elif position == 'house_leader' and event['event_type'] == 'interhouse' and user_house:
            can_manage = True
        elif position == 'event_coordinator' and event['event_type'] == 'interschool':
            can_manage = True
        elif position == 'club_leader' and user_id == event['created_by'] and event.get('club_id') == user_club_id:
            can_manage = True

        if not can_manage:
            flash('You do not have permission to manage this event', 'error')
            return redirect(url_for('dashboard'))
        
        if position == 'house_leader' and user_house:
            cursor.execute("""
                SELECT s.student_id, s.name, s.grade, s.section, u.email
                FROM registrations r
                JOIN students s ON r.student_id = s.student_id
                JOIN users u ON r.student_id = u.student_id
                WHERE r.event_id = %s AND s.house = %s
                ORDER BY s.name
            """,
            (event_id, user_house))
        else:
            cursor.execute("""
                SELECT s.student_id, s.name, s.grade, s.section, u.email
                FROM registrations r
                JOIN students s ON r.student_id = s.student_id
                JOIN users u ON r.student_id = u.student_id
                WHERE r.event_id = %s
                ORDER BY s.name
            """,
            (event_id,))
        registered_students = cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
    
    return render_template('manage_event.html', event=event, registered_students=registered_students)

@app.route('/event/add_student/<event_id>', methods=['POST'])
@login_required
def add_student_to_event(event_id):
    position = session.get('position', 'none')
    student_id = request.form.get('student_id')
    
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('dashboard'))
        
        can_manage = False
        user_house = session.get('house')
        user_club_id = session.get('club_id')
        user_id = session.get('user_id')
        
        if position == 'prefect':
            can_manage = True
        elif position == 'house_leader' and event['event_type'] == 'interhouse' and user_house:
            can_manage = True
        elif position == 'event_coordinator' and event['event_type'] == 'interschool':
            can_manage = True
        elif position == 'club_leader' and user_id == event['created_by'] and event.get('club_id') == user_club_id:
            can_manage = True

        if not can_manage:
            flash('You do not have permission to manage this event', 'error')
            return redirect(url_for('dashboard'))
        
        if position == 'house_leader' and user_house:
            cursor.execute("SELECT house FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student or student['house'] != user_house:
                flash('You can only add students from your own house to interhouse events', 'error')
                return redirect(url_for('manage_event', event_id=event_id))
        
        cursor.execute("SELECT * FROM registrations WHERE student_id = %s AND event_id = %s",
                    (student_id, event_id))
        if cursor.fetchone():
            flash('Student is already registered for this event', 'info')
            return redirect(url_for('manage_event', event_id=event_id))
        
        cursor.execute("INSERT INTO registrations (student_id, event_id) VALUES (%s, %s)",
                    (student_id, event_id))
        connection.commit()
        flash('Student added to event successfully', 'success')
        return redirect(url_for('manage_event', event_id=event_id))
    finally:
        cursor.close()
        connection.close()

@app.route('/event/remove_student/<event_id>', methods=['POST'])
@login_required
def remove_student_from_event(event_id):
    position = session.get('position', 'none')
    user_id = session.get('user_id')
    student_id = request.form.get('student_id')
    
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('dashboard'))
        
        can_manage = False
        user_house = session.get('house')
        user_club_id = session.get('club_id')
        
        if position == 'prefect':
            can_manage = True
        elif position == 'house_leader' and event['event_type'] == 'interhouse' and user_house:
            can_manage = True
        elif position == 'event_coordinator' and event['event_type'] == 'interschool':
            can_manage = True
        elif position == 'club_leader' and user_id == event['created_by'] and event.get('club_id') == user_club_id:
            can_manage = True
        
        if not can_manage:
            flash('You do not have permission to manage this event', 'error')
            return redirect(url_for('dashboard'))
        
        if position == 'house_leader' and user_house:
            cursor.execute("SELECT house FROM students WHERE student_id = %s", (student_id,))
            student = cursor.fetchone()
            if not student or student['house'] != user_house:
                flash('You can only remove students from your own house from interhouse events', 'error')
                return redirect(url_for('manage_event', event_id=event_id))
        
        cursor.execute("DELETE FROM registrations WHERE student_id = %s AND event_id = %s",
                    (student_id, event_id))
        connection.commit()
        flash('Student removed from event successfully', 'success')
        return redirect(url_for('manage_event', event_id=event_id))
    finally:
        cursor.close()
        connection.close()

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

@app.route('/event_summary/<event_id>')
@login_required
def event_summary(event_id):
    connection = get_db_connection()
    cursor = get_db_cursor(connection)
    try:
        cursor.execute("SELECT * FROM events WHERE event_id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('dashboard'))
                
    finally:
        cursor.close()
        connection.close()
    
    return render_template('event_summary.html', event=event)


if __name__ == '__main__':
    app.run(port=5001,debug=True)