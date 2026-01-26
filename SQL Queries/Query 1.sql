-- Create Database (4 tables)
CREATE DATABASE IF NOT EXISTS student_events;

USE student_events;

-- Students table. Holds Student ID(Primary Key), Name, Grade, Section, Birthdate, Gender, Email and Position (if exists)
CREATE TABLE IF NOT EXISTS students (
		student_id INT AUTO_INCREMENT PRIMARY KEY,
		name VARCHAR(100) NOT NULL,
		grade INT NOT NULL,
		section VARCHAR(10) NOT NULL,
		birthdate DATE NOT NULL,
		gender ENUM('G', 'B') NOT NULL,
		email VARCHAR(100) UNIQUE NOT NULL,
		house ENUM('Pioneers', 'Challengers', 'Explorers', 'Voyagers') NOT NULL,
        club_id VARCHAR(100) NULL,
		position ENUM('none', 'house_leader', 'event_coordinator', 'club_leader', 'prefect') DEFAULT 'none'
	);

-- Users table. Holds Student ID(Primary Key), Email, Password (Hashed), Created time, Position (if exists), refer Student ID for remaining data
CREATE TABLE IF NOT EXISTS users (
		student_id INT PRIMARY KEY,
		email VARCHAR(100) UNIQUE NOT NULL,
		password VARCHAR(255) NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		position ENUM('none', 'house_leader', 'event_coordinator', 'club_leader', 'prefect') DEFAULT 'none',
		FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
	);
    
-- Events table. Holds Event ID (generated, Primary Key), Event Name, Event type, Grades, Ages, Gender, Main Event (if exists), Created time (logging purposes)
CREATE TABLE IF NOT EXISTS events (
		event_id VARCHAR(50) PRIMARY KEY,
		event_name VARCHAR(200) NOT NULL,
		event_type ENUM('interhouse', 'interschool') NOT NULL,
		grades_eligible VARCHAR(50),
		ages_eligible VARCHAR(50),
		gender ENUM('G', 'B', 'A') DEFAULT 'A',
		main_event VARCHAR(200),
		last_registration_date DATE NOT NULL,
		event_date DATE NOT NULL,
		created_by INT NOT NULL,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		event_summary TEXT,
		club_id VARCHAR(100) NULL
	);

-- Registrations table, Reg. ID(Primary Key), Student ID, Event ID, Registered time, refer Student ID and Event ID for remaining data
-- Unique Key, Student ID + Event ID   
CREATE TABLE IF NOT EXISTS registrations (
		registration_id INT AUTO_INCREMENT PRIMARY KEY,
		student_id INT NOT NULL,
		event_id VARCHAR(50) NOT NULL,
		registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
		FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
		UNIQUE KEY unique_registration (student_id, event_id)
	);

CREATE TABLE IF NOT EXISTS admin (
	id INT AUTO_INCREMENT PRIMARY KEY,
	name VARCHAR(100) NOT NULL,
	email VARCHAR(100) UNIQUE NOT NULL,
	password VARCHAR(255) NOT NULL,
	otp_secret VARCHAR(32),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS clubs (
		club_id VARCHAR(100) PRIMARY KEY,
		club_name VARCHAR(200) NOT NULL
	);
