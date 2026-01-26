USE student_events;

INSERT INTO clubs (club_id, club_name)
VALUES 
(1, 'Science Club'),
(2, 'Lit Club'),
(3, 'Art Club'),
(4, 'Math Club'),
(5, 'History Club'),
(6, 'Music Club'),
(7, 'Theatre Club'),
(8, 'Dance Club'),
(9, 'Sports Club'),
(10, 'STEM Club');

INSERT INTO admin (name, email, password, otp_secret)
VALUES 
('Orange Juice', 'orange@admin.com', '$argon2id$v=19$m=65536,t=3,p=4$77yz5MyWcIs/LOyuI69Hjg$Y7iM4SxvzDlYY/8Av2flu2QWT0uT2ekIbJm736l1WQU', 'check')
