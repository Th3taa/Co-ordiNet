-- Apply after creating the base tables, or once to upgrade an existing database.
ALTER TABLE events
    ADD COLUMN eligibility_type ENUM('grade', 'age') NOT NULL DEFAULT 'grade' AFTER event_type;

ALTER TABLE notifications
    MODIFY COLUMN notification_type ENUM('announcement', 'reminder', 'event_created') NOT NULL;
