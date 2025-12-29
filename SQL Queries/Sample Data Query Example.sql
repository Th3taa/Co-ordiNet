USE student_events;

SELECT students;

-- Execute Query 1 b4 running this
-- Generate 30-40 students per grade for now, we can expand later
INSERT INTO students (name, grade, section, birthdate, gender, email, house, club_id, position)
VALUES ('Orange Juice', 12, 'A', 2007-12-19, 'B', 'orangejuice0001@school.com', 'Pioneers', 'Juice Club', 'club_leader'),
	   ('Tomato Sauce', 12, 'A', 2008-04-06, 'G', 'tomatosauce0002@school.com', 'Challengers', NULL, 'house_leader'),
       ('Blue Cheese', 12, 'B', 2008-05-28, 'bluecheese0003@school.com', 'Voyagers', NULL, 'prefect')
 