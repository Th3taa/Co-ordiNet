USE co_ordinet;

CREATE TABLE students (
    student_id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    grade INT NOT NULL,
    section VARCHAR(10) NOT NULL,
    birthdate DATE NOT NULL,
    gender ENUM('M', 'F') NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    house ENUM('Pioneers', 'Challengers', 'Explorers', 'Voyagers') NOT NULL,
    position ENUM('none', 'house_captain', 'event_coordinator', 'club_leader', 'prefect') NOT NULL DEFAULT 'none',
    club_id INT NULL,
    CONSTRAINT chk_students_grade CHECK (grade BETWEEN 1 AND 12)
);

CREATE TABLE users (
    student_id INT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    otp_secret VARCHAR(64) NOT NULL,
    CONSTRAINT fk_users_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE RESTRICT
);

CREATE TABLE events (
    event_id VARCHAR(80) PRIMARY KEY,
    event_name VARCHAR(200) NOT NULL,
    event_type ENUM('interhouse', 'interschool') NOT NULL,
    grades_eligible JSON NOT NULL,
    ages_eligible JSON NOT NULL,
    gender ENUM('G', 'B', 'A') NOT NULL,
    main_event VARCHAR(200) NULL,
    last_nomination_date DATE NOT NULL,
    event_date DATE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_by INT NOT NULL,
    event_summary TEXT NOT NULL,
    associated_members JSON NOT NULL,
    CONSTRAINT fk_events_organizer FOREIGN KEY (created_by) REFERENCES users(student_id) ON DELETE RESTRICT,
    CONSTRAINT chk_event_dates CHECK (event_date > last_nomination_date)
);

CREATE TABLE nominations (
    nomination_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    event_id VARCHAR(80) NOT NULL,
    nominated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('Nominated', 'Selected', 'Pending Approval') NOT NULL,
    CONSTRAINT uq_nominations_student_event UNIQUE (student_id, event_id),
    CONSTRAINT fk_nominations_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_nominations_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE
);

CREATE TABLE participants (
    participation_id INT AUTO_INCREMENT PRIMARY KEY,
    student_id INT NOT NULL,
    event_id VARCHAR(80) NOT NULL,
    selected_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    selected_by INT NOT NULL,
    withdrawal_status ENUM('none', 'To be approved') NOT NULL DEFAULT 'none',
    CONSTRAINT uq_participants_student_event UNIQUE (student_id, event_id),
    CONSTRAINT fk_participants_student FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_participants_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    CONSTRAINT fk_participants_selector FOREIGN KEY (selected_by) REFERENCES users(student_id) ON DELETE RESTRICT
);

CREATE TABLE notifications (
    notification_id INT AUTO_INCREMENT PRIMARY KEY,
    event_id VARCHAR(80) NOT NULL,
    recipient_id INT NULL,
    authored_by INT NULL,
    notification_type ENUM('announcement', 'reminder') NOT NULL,
    notification_key VARCHAR(100) NULL UNIQUE,
    title VARCHAR(200) NOT NULL,
    body TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_notifications_event FOREIGN KEY (event_id) REFERENCES events(event_id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_recipient FOREIGN KEY (recipient_id) REFERENCES users(student_id) ON DELETE CASCADE,
    CONSTRAINT fk_notifications_author FOREIGN KEY (authored_by) REFERENCES users(student_id) ON DELETE SET NULL
);
