"""Run once a day with a system scheduler after the Flask application is configured."""
import datetime

from app import database


def create_reminder(cursor, event_id: str, student_id: int, reminder_key: str, title: str, body: str) -> None:
    cursor.execute(
        """INSERT IGNORE INTO notifications (event_id, recipient_id, notification_type, notification_key, title, body) VALUES (%s, %s, 'reminder', %s, %s, %s)""",
        (event_id, student_id, reminder_key, title, body),
    )


def run_reminders() -> None:
    today = datetime.date.today()
    with database() as (_, cursor):
        cursor.execute(
            "DELETE nominations FROM nominations JOIN events ON events.event_id = nominations.event_id WHERE nominations.status = 'Pending Approval' AND events.last_nomination_date < %s",
            (today,),
        )
        cursor.execute("SELECT * FROM events WHERE event_date >= %s", (today,))
        events = cursor.fetchall()
        for event in events:
            cursor.execute("SELECT student_id FROM participants WHERE event_id = %s", (event["event_id"],))
            participant_ids = [row["student_id"] for row in cursor.fetchall()]
            for days, label in ((7, "one week"), (1, "tomorrow"), (0, "today")):
                if event["event_date"] == today + datetime.timedelta(days=days):
                    for student_id in participant_ids:
                        create_reminder(
                            cursor,
                            event["event_id"],
                            student_id,
                            f"event-{event['event_id']}-{days}-{today.isoformat()}",
                            f"Event {label}: {event['event_name']}",
                            f"Your event is on {event['event_date']:%d %b %Y}.",
                        )
                if event["last_nomination_date"] == today + datetime.timedelta(days=days):
                    cursor.execute("SELECT student_id FROM users")
                    for row in cursor.fetchall():
                        create_reminder(
                            cursor,
                            event["event_id"],
                            row["student_id"],
                            f"deadline-{event['event_id']}-{days}-{today.isoformat()}",
                            f"Nomination deadline {label}: {event['event_name']}",
                            f"Nominations close on {event['last_nomination_date']:%d %b %Y}.",
                        )


if __name__ == "__main__":
    run_reminders()
