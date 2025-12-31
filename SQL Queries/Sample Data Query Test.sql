USE student_events;

-- Test Data
INSERT INTO student_events.students (name, grade, section, birthdate, gender, email, house, club_id, position) VALUES
('Orange Juice', '12', 'A', '2007-12-19', 'B', 'orangejuice0001@school.com', 'Pioneers', 'Juice Club', 'club_leader'),
('Admin User', '0', 'Admin', '2005-01-01', 'B', 'admin@school.com', 'Pioneers', NULL, 'prefect'),
('Tomato Sauce', '12', 'A', '2008-04-06', 'G', 'tomatosauce0003@school.com', 'Challengers', NULL, 'house_leader'),
('Blue Cheese', '12', 'B', '2008-05-28', 'B', 'bluecheese0004@school.com', 'Voyagers', NULL, 'prefect');
