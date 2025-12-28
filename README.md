# Project-Coordinet

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

## Database Schema

### Students Table
- `student_id` (INT, Primary Key, Auto Increment)
- `name` (VARCHAR(100))
- `grade` (INT)
- `section` (VARCHAR(10))
- `birthdate` (DATE)
- `gender` (ENUM: 'M', 'F')
- `email` (VARCHAR(100), Unique)
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
- `created_at` (TIMESTAMP)

### Registrations Table
- `registration_id` (INT, Primary Key, Auto Increment)
- `student_id` (INT, Foreign Key)
- `event_id` (VARCHAR(50), Foreign Key)
- `registered_at` (TIMESTAMP)
- Unique constraint on (student_id, event_id)

## License
This project is for educational purposes.
