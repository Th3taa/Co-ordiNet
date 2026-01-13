# Student Events Management System

A Flask-based web application for managing interschool and interhouse events, with role-based access control for students and student council members.

## Features

### Student Features
- View all events (displayed as notices)
- Register for events
- Unregister from events
- Automatic eligibility checking based on grade, age, and gender

### Student Council Roles

1. **House Leaders**
   - Add/remove students from interhouse events

2. **Event Coordinators**
   - Create interschool events
   - Add/remove students from interschool events

3. **Club Leaders**
   - Create both interhouse and interschool events
   - Add/remove students from interschool events

4. **Prefects**
   - Complete access to all events
   - Can create and manage all event types
   - Can add/remove students from any event

## Event ID Format

The grades are given in Hexadecimal to prevent any overlaps or double digits

{
   1:1,
   2:2,
   3:3,
   4:4,
   5:5,
   6:6,
   7:7,
   8:8,
   9:9,
   10:A,
   11:B,
   12:C
}

### Interhouse Events
Format: `IH{CLUB_NO:2}{GRADE_RANGE_HEX}{GENDER}`
- Example: `IH015-CA` (Club 1, Grades 5-12, All genders)
- Example: `IH378-BG` (Club 37, Grades 8-11, Girls Only)

### Interschool Events
Format: `IS{NEXT_NO:4}{GENDER}${GRADES}{$MAIN_EVENT}`
- Example: `IS0001A$123456789ABC` (Event 1, All grades, All genders)
- Example: `IS0002A$6789ABC$SportsFest` (Event 2, Sub-event of SportsFest, Grades 6-12, All Genders)

## Setup Instructions

### Prerequisites
- Python 3.7+
- MySQL Server
- pip

### Installation

1. **Install Python dependencies:**
   ```
   pip install -r requirements.txt
   ```

2. **Configure MySQL:**
   - Make sure MySQL is running
   - Update database credentials in `app.py` if needed:
     ```python
     MYSQL_CONFIG = {
         'host': 'localhost',
         'user': 'root',
         'password': '***',
         'database': 'student_events'
     }
     ```

3. **Initialize the database:**
   ```
   python init_db.py
   ```
   This will create:
   - The `student_events` database
   - All required tables (students, events, registrations)
   - A sample admin user (email: `admin@school.com`, password: `admin123`)

4. **Run the application:**
   ```
   python app.py
   ```

5. **Access the application:**
   - Open your browser and go to `http://localhost:5001`
   - Login with an existing account or register a new account

## Database Schema

### Students Table
- `student_id` (INT, Primary Key, Auto Increment)
- `name` (VARCHAR(100))
- `grade` (INT)
- `section` (VARCHAR(10))
- `birthdate` (DATE)
- `gender` (ENUM: 'M', 'F')
- `email` (VARCHAR(100), Unique)
- `house` (ENUM: 'Pioneers', 'Challengers', 'Explorers', 'Voyagers')
- `club_id` (VARCHAR(100), nullable)
- `position` (ENUM: 'none', 'house_leader', 'event_coordinator', 'club_leader', 'prefect')

### Users Table
- `student_id` (INT, Primary Key, Auto Increment)
- `email` (VARCHAR(100), Unique)
- `password` (VARCHAR(255), Argon2 hashed)
- `created_at` (TIMESTAMP)
- `position` (ENUM: 'none', 'house_leader', 'event_coordinator', 'club_leader', 'prefect')

### Events Table
- `event_id` (VARCHAR(50), Primary Key)
- `event_name` (VARCHAR(200))
- `event_type` (ENUM: 'interhouse', 'interschool')
- `grades_eligible` (VARCHAR(50), comma-separated)
- `ages_eligible` (VARCHAR(50))
- `gender` (ENUM: 'G', 'B', 'A')
- `main_event` (VARCHAR(200), nullable)
- `last_registration_date` (DATE)
- `event_date` (DATE)
- `club_id` (VARCHAR(100), nullable)
- `created_at` (TIMESTAMP)
- `created_by` (INT)
- `event_summary` (TEXT)

### Registrations Table
- `registration_id` (INT, Primary Key, Auto Increment)
- `student_id` (INT, Foreign Key)
- `event_id` (VARCHAR(50), Foreign Key)
- `registered_at` (TIMESTAMP)
- Unique constraint on (student_id, event_id)

### Admin Table
- `id` (INT, Primary Key, Auto Increment)
- `name` (VARCHAR(100))
- `email` (VARCHAR(100), Unique)
- `password` (VARCHAR(255), Argon2 hashed)
- `OTP key` (VARCHAR(255))
- `created_at` (TIMESTAMP)

## Usage

### For Students
1. Register/Login to the system
2. View all available events on the dashboard
3. Click "Register" to join an event
4. Click "Unregister" to leave an event

### For Student Council Members
1. Login with your council member account
2. Click "Create Event" to add new events
3. Click "Manage" on any event you have permission to manage
4. Use the search function to add students to events
5. Remove students from events as needed

## Security Features
- Password hashing using Argon2
- Session-based authentication
- Role-based access control
- SQL injection protection (parameterized queries)
- CSRF protection (Flask sessions)
- pyotp for OTP admin login

## Notes
- Event IDs are automatically generated based on the event type and parameters
- Students can only register for events they are eligible for
- Eligibility is checked based on grade, age, and gender
- All events are displayed as notices on the dashboard
- Main events can contain multiple sub-events

## Troubleshooting

### Database Connection Issues
- Ensure MySQL server is running
- Check database credentials in `app.py`
- Verify the database exists (run `init_db.py` or the SQL Queries)

### Import Errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`

### Permission Errors
- Check that your user account has the correct `position` value in the database
- Prefects have access to all features

## License
This project is for educational purposes.

## Contributors
- Dasmat Ajmani (Dasmax264)
- Ira Agarwal (idktbhyay)
- Swapnil Basu (Th3taa, bruhdrone)


