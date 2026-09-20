import datetime
import json
import os
from contextlib import contextmanager
from functools import wraps

import mysql.connector
import pyotp
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, session, url_for

from utils import age_from_dob, event_id_ih, event_id_is, tgt_name

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "change-this-before-production")
password_hash = PasswordHasher()
role_names = {
    "none": "Student",
    "house_captain": "House Captain",
    "event_coordinator": "Event Coordinator",
    "club_leader": "Club Leader",
    "prefect": "Prefect",
}


def database_config() -> dict:
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", "sql123"),
        "database": os.getenv("MYSQL_DATABASE", "co_ordinet"),
    }


@contextmanager
def database():
    connection = mysql.connector.connect(**database_config())
    cursor = connection.cursor(dictionary=True)
    try:
        yield connection, cursor
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def fetch_one(query: str, values: tuple = ()) -> dict | None:
    with database() as (_, cursor):
        cursor.execute(query, values)
        return cursor.fetchone()


def fetch_all(query: str, values: tuple = ()) -> list[dict]:
    with database() as (_, cursor):
        cursor.execute(query, values)
        return cursor.fetchall()


def current_user() -> dict | None:
    student_id = session.get("student_id")
    if not student_id:
        return None
    return fetch_one(
        """
        SELECT students.*, users.email AS login_email FROM students
        JOIN users ON users.student_id = students.student_id
        WHERE students.student_id = %s
    """,
        (student_id,),
    )


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not current_user():
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


def parse_json(value: object) -> list:
    if isinstance(value, str):
        return json.loads(value)
    return value or []


def is_council(user: dict) -> bool:
    return user["position"] != "none"


def can_create(user: dict, event_type: str) -> bool:
    return user["position"] in {"prefect", "club_leader"} or (
        user["position"] == "event_coordinator" and event_type == "interschool"
    )


def automatic_member_ids(event_type: str) -> list[int]:
    positions = ["prefect"]
    if event_type == "interhouse":
        positions.append("house_captain")
    else:
        positions.append("event_coordinator")
    marks = ", ".join(["%s"] * len(positions))
    rows = fetch_all(f"SELECT student_id FROM students WHERE position IN ({marks})", tuple(positions))
    return [row["student_id"] for row in rows]


def can_manage_event(user: dict, event: dict) -> bool:
    associated_ids = [int(value) for value in parse_json(event["associated_members"])]
    return user["student_id"] in associated_ids or user["student_id"] in automatic_member_ids(event["event_type"])


def event_eligibility(event: dict, student: dict) -> str | None:
    grades = [int(value) for value in parse_json(event["grades_eligible"])]
    ages = [int(value) for value in parse_json(event["ages_eligible"])]
    if student["grade"] not in grades:
        return "Your grade is not eligible for this event."
    age = age_from_dob(student["birthdate"], event["event_date"])
    if ages and age not in ages:
        return "Your age on the event date is not eligible for this event."
    if event["gender"] != "A" and event["gender"] != ("B" if student["gender"] == "M" else "G"):
        return "Your gender is not eligible for this event."
    return None


def event_from_id(event_id: str) -> dict:
    event = fetch_one("SELECT * FROM events WHERE event_id = %s", (event_id,))
    if not event:
        abort(404)
    return event


def form_event() -> tuple[dict | None, str | None]:
    event_type = request.form.get("event_type", "")
    event_name = request.form.get("event_name", "").strip()
    main_event = request.form.get("main_event", "").strip() or None
    summary = request.form.get("event_summary", "").strip()
    gender = request.form.get("gender", "")
    try:
        grades = sorted({int(value) for value in request.form.getlist("grades")})
        ages = sorted({int(value) for value in request.form.getlist("ages")})
        deadline = datetime.date.fromisoformat(request.form["last_nomination_date"])
        event_date = datetime.date.fromisoformat(request.form["event_date"])
        club_id = int(request.form.get("club_id", "0")) if event_type == "interhouse" else None
        extra_members = {int(value) for value in request.form.getlist("associated_members")}
    except (KeyError, TypeError, ValueError):
        return None, "Please provide valid dates, grades, ages, and council-member IDs."
    if event_type not in {"interhouse", "interschool"} or gender not in {"A", "B", "G"}:
        return None, "Choose a valid event type and gender eligibility."
    if not event_name or not summary or not grades or not ages:
        return None, "Event name, summary, at least one grade, and at least one age are required."
    if deadline <= datetime.date.today() or event_date <= deadline:
        return None, "The nomination deadline must be in the future and before the event date."
    if event_type == "interhouse" and (not club_id or not 1 <= club_id <= 99):
        return None, "Interhouse events need a club number from 1 to 99."
    if event_type == "interhouse":
        main_event = None
        if grades != list(range(min(grades), max(grades) + 1)):
            return None, "Interhouse IDs represent a grade range, so choose consecutive grades."
    if extra_members:
        marks = ", ".join(["%s"] * len(extra_members))
        council_rows = fetch_all(
            f"SELECT student_id FROM students WHERE position != 'none' AND student_id IN ({marks})",
            tuple(extra_members),
        )
        if {row["student_id"] for row in council_rows} != extra_members:
            return None, "Only student council members can be associated with an event."
    return {
        "event_type": event_type,
        "event_name": event_name,
        "main_event": main_event,
        "event_summary": summary,
        "gender": gender,
        "grades": grades,
        "ages": ages,
        "last_nomination_date": deadline,
        "event_date": event_date,
        "club_id": club_id,
        "associated_members": extra_members,
    }, None


@app.context_processor
def shared_template_data() -> dict:
    current_user_data = current_user()
    return {
        "CurrentUser": current_user_data,
        "current_user": current_user_data,
        "RoleNames": role_names,
        "role_names": role_names,
        "Today": datetime.date.today(),
        "today": datetime.date.today(),
        "ParseJson": parse_json,
        "parse_json": parse_json,
    }


@app.route("/")
def home():
    if not current_user():
        return redirect(url_for("login"))
    user = current_user()
    counts = {
        "events": fetch_one("SELECT COUNT(*) AS count FROM events WHERE event_date >= CURDATE()")["count"],
        "participating": fetch_one("SELECT COUNT(*) AS count FROM participants WHERE student_id = %s", (user["student_id"],))["count"],
        "notifications": fetch_one("SELECT COUNT(*) AS count FROM notifications WHERE recipient_id IS NULL OR recipient_id = %s", (user["student_id"],))["count"],
    }
    events = fetch_all("SELECT * FROM events WHERE event_date >= CURDATE() ORDER BY event_date LIMIT 5")
    return render_template("home.html", Counts=counts, counts=counts, Events=events, events=events)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        fields = ["student_id", "first_name", "last_name", "birthdate", "grade", "section", "gender", "email", "house", "password"]
        if any(not request.form.get(field, "").strip() for field in fields):
            flash("All required fields must be filled in.", "error")
        else:
            try:
                student_id = int(request.form["student_id"])
                name = tgt_name(request.form["first_name"], request.form.get("middle_name"), request.form["last_name"])
                student = fetch_one("SELECT * FROM students WHERE student_id = %s", (student_id,))
                birthdate = datetime.date.fromisoformat(request.form["birthdate"])
                matches = (
                    student
                    and student["name"] == name
                    and student["birthdate"] == birthdate
                    and student["grade"] == int(request.form["grade"])
                    and student["section"] == request.form["section"].strip()
                    and student["gender"] == request.form["gender"]
                    and student["email"].lower() == request.form["email"].lower()
                    and student["house"] == request.form["house"]
                )
                if not matches:
                    flash("Those details do not match the school record.", "error")
                elif fetch_one("SELECT student_id FROM users WHERE student_id = %s OR email = %s", (student_id, request.form["email"].lower())):
                    flash("This student is already registered.", "error")
                else:
                    with database() as (_, cursor):
                        cursor.execute(
                            "INSERT INTO users (student_id, email, password, otp_secret) VALUES (%s, %s, %s, %s)",
                            (student_id, request.form["email"].lower(), password_hash.hash(request.form["password"]), pyotp.random_base32()),
                        )
                    flash("Registration complete. You can now log in.", "success")
                    return redirect(url_for("login"))
            except (ValueError, KeyError):
                flash("Please enter valid registration details.", "error")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        user = fetch_one("SELECT * FROM users WHERE CAST(student_id AS CHAR) = %s OR email = %s", (identifier, identifier.lower()))
        try:
            valid = user and password_hash.verify(user["password"], password)
        except VerifyMismatchError:
            valid = False
        if not valid:
            flash("Invalid login details.", "error")
        else:
            otp = pyotp.TOTP(user["otp_secret"]).now()
            print(f"Co-ordinet login OTP for student {user['student_id']}: {otp}")
            session["pending_login"] = user["student_id"]
            flash("An OTP was printed in the Flask terminal for this demo.", "success")
            return redirect(url_for("verify_login_otp"))
    return render_template("login.html")


@app.route("/login/verify", methods=["GET", "POST"])
def verify_login_otp():
    student_id = session.get("pending_login")
    if not student_id:
        return redirect(url_for("login"))
    if request.method == "POST":
        user = fetch_one("SELECT * FROM users WHERE student_id = %s", (student_id,))
        if user and pyotp.TOTP(user["otp_secret"]).verify(request.form.get("otp", ""), valid_window=1):
            session.clear()
            session["student_id"] = student_id
            return redirect(url_for("home"))
        flash("That OTP is invalid or expired.", "error")
    return render_template("otp.html", Purpose="Log in")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/events")
@login_required
def events():
    search = request.args.get("q", "").strip()
    query = "SELECT * FROM events WHERE event_date >= CURDATE()"
    values: tuple = ()
    if search:
        query += " AND (event_name LIKE %s OR main_event LIKE %s)"
        values = (f"%{search}%", f"%{search}%")
    query += " ORDER BY event_date, event_name"
    return render_template("events.html", Events=fetch_all(query, values), Search=search)


@app.route("/events/<event_id>")
@login_required
def event_detail(event_id: str):
    event = event_from_id(event_id)
    user = current_user()
    nomination = fetch_one("SELECT * FROM nominations WHERE event_id = %s AND student_id = %s", (event_id, user["student_id"]))
    participant = fetch_one("SELECT * FROM participants WHERE event_id = %s AND student_id = %s", (event_id, user["student_id"]))
    return render_template(
        "event_detail.html",
        Event=event,
        Nomination=nomination,
        Participant=participant,
        CanManage=can_manage_event(user, event),
        Eligibility=event_eligibility(event, user),
    )


@app.route("/events/create", methods=["GET", "POST"])
@login_required
def create_event():
    user = current_user()
    council = fetch_all("SELECT student_id, name, position FROM students WHERE position != 'none' ORDER BY name")
    if request.method == "POST":
        data, error = form_event()
        if error:
            flash(error, "error")
        elif not can_create(user, data["event_type"]):
            abort(403)
        else:
            members = data["associated_members"] | set(automatic_member_ids(data["event_type"])) | {user["student_id"]}
            if data["event_type"] == "interhouse":
                event_id = event_id_ih(data["club_id"], set(data["grades"]), data["gender"])
            else:
                row = fetch_one("SELECT COALESCE(MAX(CAST(SUBSTRING(event_id, 3, 4) AS UNSIGNED)), 0) + 1 AS next_number FROM events WHERE event_type = 'interschool'")
                event_id = event_id_is(row["next_number"], data["grades"], data["gender"], data["main_event"])
            if fetch_one("SELECT event_id FROM events WHERE event_id = %s", (event_id,)):
                flash("An event with this generated ID already exists. Change the eligible range or club number.", "error")
                return render_template("event_form.html", Event=None, Council=council)
            with database() as (_, cursor):
                cursor.execute(
                    """INSERT INTO events (event_id, event_name, event_type, grades_eligible, ages_eligible, gender, main_event, last_nomination_date, event_date, created_by, event_summary, associated_members) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        event_id,
                        data["event_name"],
                        data["event_type"],
                        json.dumps(data["grades"]),
                        json.dumps(data["ages"]),
                        data["gender"],
                        data["main_event"],
                        data["last_nomination_date"],
                        data["event_date"],
                        user["student_id"],
                        data["event_summary"],
                        json.dumps(sorted(members)),
                    ),
                )
            flash(f"Event {event_id} was created.", "success")
            return redirect(url_for("event_detail", event_id=event_id))
    return render_template("event_form.html", Event=None, Council=council)


@app.route("/events/<event_id>/edit", methods=["GET", "POST"])
@login_required
def edit_event(event_id: str):
    event = event_from_id(event_id)
    user = current_user()
    if not can_manage_event(user, event):
        abort(403)
    council = fetch_all("SELECT student_id, name, position FROM students WHERE position != 'none' ORDER BY name")
    if request.method == "POST":
        data, error = form_event()
        if error:
            flash(error, "error")
        elif data["event_type"] != event["event_type"]:
            flash("Event type cannot be changed after creation.", "error")
        else:
            members = data["associated_members"] | set(automatic_member_ids(event["event_type"])) | {event["created_by"]}
            with database() as (_, cursor):
                cursor.execute(
                    """UPDATE events SET event_name = %s, grades_eligible = %s, ages_eligible = %s, gender = %s, main_event = %s, last_nomination_date = %s, event_date = %s, event_summary = %s, associated_members = %s WHERE event_id = %s""",
                    (
                        data["event_name"],
                        json.dumps(data["grades"]),
                        json.dumps(data["ages"]),
                        data["gender"],
                        data["main_event"],
                        data["last_nomination_date"],
                        data["event_date"],
                        data["event_summary"],
                        json.dumps(sorted(members)),
                        event_id,
                    ),
                )
            flash("Event updated.", "success")
            return redirect(url_for("event_detail", event_id=event_id))
    return render_template("event_form.html", Event=event, Council=council)


@app.post("/events/<event_id>/delete")
@login_required
def delete_event(event_id: str):
    event = event_from_id(event_id)
    if not can_manage_event(current_user(), event):
        abort(403)
    with database() as (_, cursor):
        cursor.execute("DELETE FROM events WHERE event_id = %s", (event_id,))
    flash("Event deleted.", "success")
    return redirect(url_for("events"))


@app.post("/events/<event_id>/nominate")
@login_required
def self_nominate(event_id: str):
    event = event_from_id(event_id)
    user = current_user()
    error = event_eligibility(event, user)
    if error:
        flash(error, "error")
    elif event["last_nomination_date"] < datetime.date.today():
        flash("The nomination deadline has passed.", "error")
    else:
        try:
            with database() as (_, cursor):
                cursor.execute("INSERT INTO nominations (student_id, event_id, status) VALUES (%s, %s, 'Nominated')", (user["student_id"], event_id))
            flash("You are nominated for this event.", "success")
        except mysql.connector.IntegrityError:
            flash("You already have a nomination for this event.", "error")
    return redirect(url_for("event_detail", event_id=event_id))


@app.post("/nominations/<int:nomination_id>/respond")
@login_required
def respond_nomination(nomination_id: int):
    nomination = fetch_one("SELECT * FROM nominations WHERE nomination_id = %s", (nomination_id,))
    if not nomination or nomination["student_id"] != current_user()["student_id"] or nomination["status"] != "Pending Approval":
        abort(403)
    with database() as (_, cursor):
        if request.form.get("response") == "accept":
            cursor.execute("UPDATE nominations SET status = 'Nominated' WHERE nomination_id = %s", (nomination_id,))
            flash("Nomination accepted.", "success")
        else:
            cursor.execute("DELETE FROM nominations WHERE nomination_id = %s", (nomination_id,))
            flash("Nomination declined.", "success")
    return redirect(url_for("notifications"))


@app.route("/events/<event_id>/participants", methods=["GET", "POST"])
@login_required
def participants(event_id: str):
    event = event_from_id(event_id)
    user = current_user()
    if not can_manage_event(user, event):
        abort(403)
    if request.method == "POST":
        try:
            student_id = int(request.form["student_id"])
            student = fetch_one("SELECT * FROM students WHERE student_id = %s", (student_id,))
            error = None if student else "Student not found."
            error = error or event_eligibility(event, student)
            if error:
                flash(error, "error")
            else:
                with database() as (_, cursor):
                    cursor.execute("INSERT INTO nominations (student_id, event_id, status) VALUES (%s, %s, 'Pending Approval')", (student_id, event_id))
                flash("Nomination sent for the student's approval.", "success")
        except (ValueError, KeyError, mysql.connector.IntegrityError):
            flash("That student already has a nomination or the ID is invalid.", "error")
    nominations = fetch_all("SELECT nominations.*, students.name, students.grade, students.house FROM nominations JOIN students ON students.student_id = nominations.student_id WHERE nominations.event_id = %s ORDER BY nominations.nominated_at", (event_id,))
    participants_list = fetch_all("SELECT participants.*, students.name, students.grade, students.house FROM participants JOIN students ON students.student_id = participants.student_id WHERE participants.event_id = %s ORDER BY students.name", (event_id,))
    return render_template("participants.html", Event=event, Nominations=nominations, Participants=participants_list)


@app.post("/events/<event_id>/nominations/<int:nomination_id>/<action>")
@login_required
def manage_nomination(event_id: str, nomination_id: int, action: str):
    event = event_from_id(event_id)
    if not can_manage_event(current_user(), event):
        abort(403)
    nomination = fetch_one("SELECT * FROM nominations WHERE nomination_id = %s AND event_id = %s", (nomination_id, event_id))
    if not nomination:
        abort(404)
    with database() as (_, cursor):
        if action == "select" and nomination["status"] == "Nominated":
            cursor.execute("INSERT INTO participants (student_id, event_id, selected_by) VALUES (%s, %s, %s)", (nomination["student_id"], event_id, current_user()["student_id"]))
            cursor.execute("UPDATE nominations SET status = 'Selected' WHERE nomination_id = %s", (nomination_id,))
            flash("Student selected.", "success")
        elif action == "disqualify":
            cursor.execute("DELETE FROM participants WHERE student_id = %s AND event_id = %s", (nomination["student_id"], event_id))
            cursor.execute("DELETE FROM nominations WHERE nomination_id = %s", (nomination_id,))
            flash("Nomination removed.", "success")
        else:
            flash("That action is not available for this nomination.", "error")
    return redirect(url_for("participants", event_id=event_id))


@app.post("/events/<event_id>/withdraw")
@login_required
def request_withdrawal(event_id: str):
    participant = fetch_one("SELECT * FROM participants WHERE event_id = %s AND student_id = %s", (event_id, current_user()["student_id"]))
    if not participant:
        abort(404)
    with database() as (_, cursor):
        cursor.execute("UPDATE participants SET withdrawal_status = 'To be approved' WHERE participation_id = %s", (participant["participation_id"],))
    flash("Your withdrawal request was sent to the event managers.", "success")
    return redirect(url_for("event_detail", event_id=event_id))


@app.post("/events/<event_id>/participants/<int:participation_id>/withdrawal")
@login_required
def approve_withdrawal(event_id: str, participation_id: int):
    event = event_from_id(event_id)
    if not can_manage_event(current_user(), event):
        abort(403)
    participant = fetch_one("SELECT * FROM participants WHERE participation_id = %s AND event_id = %s", (participation_id, event_id))
    if not participant or participant["withdrawal_status"] != "To be approved":
        abort(404)
    with database() as (_, cursor):
        if request.form.get("decision") == "approve":
            cursor.execute("DELETE FROM participants WHERE participation_id = %s", (participation_id,))
            cursor.execute("DELETE FROM nominations WHERE student_id = %s AND event_id = %s", (participant["student_id"], event_id))
            flash("Withdrawal approved.", "success")
        else:
            cursor.execute("UPDATE participants SET withdrawal_status = 'none' WHERE participation_id = %s", (participation_id,))
            flash("Withdrawal declined.", "success")
    return redirect(url_for("participants", event_id=event_id))


@app.route("/notifications")
@login_required
def notifications():
    user = current_user()
    pending = fetch_all(
        "SELECT nominations.*, events.event_name FROM nominations JOIN events ON events.event_id = nominations.event_id WHERE nominations.student_id = %s AND nominations.status = 'Pending Approval' AND events.last_nomination_date >= CURDATE()",
        (user["student_id"],),
    )
    items = fetch_all(
        "SELECT notifications.*, events.event_name FROM notifications JOIN events ON events.event_id = notifications.event_id WHERE notifications.recipient_id IS NULL OR notifications.recipient_id = %s ORDER BY notifications.published_at DESC",
        (user["student_id"],),
    )
    return render_template("notifications.html", Items=items, Pending=pending)


@app.route("/events/<event_id>/announcements", methods=["GET", "POST"])
@login_required
def announcements(event_id: str):
    event = event_from_id(event_id)
    if not can_manage_event(current_user(), event):
        abort(403)
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if title and body:
            with database() as (_, cursor):
                cursor.execute(
                    "INSERT INTO notifications (event_id, authored_by, notification_type, title, body) VALUES (%s, %s, 'announcement', %s, %s)",
                    (event_id, current_user()["student_id"], title, body),
                )
            flash("Announcement published.", "success")
            return redirect(url_for("event_detail", event_id=event_id))
        flash("A title and message are required.", "error")
    return render_template("announcement_form.html", Event=event)


@app.route("/calendar")
@login_required
def calendar():
    events = fetch_all("SELECT event_id, event_name, event_date, last_nomination_date FROM events WHERE event_date >= CURDATE() ORDER BY event_date")
    return render_template("calendar.html", Events=events)


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    if request.method == "POST":
        account = fetch_one("SELECT * FROM users WHERE student_id = %s", (user["student_id"],))
        otp = pyotp.TOTP(account["otp_secret"]).now()
        print(f"Co-ordinet password reset OTP for student {user['student_id']}: {otp}")
        session["reset_student_id"] = user["student_id"]
        return redirect(url_for("reset_password"))
    return render_template("profile.html", User=user)


@app.route("/profile/reset", methods=["GET", "POST"])
@login_required
def reset_password():
    student_id = session.get("reset_student_id")
    if student_id != current_user()["student_id"]:
        return redirect(url_for("profile"))
    if request.method == "POST":
        account = fetch_one("SELECT * FROM users WHERE student_id = %s", (student_id,))
        new_password = request.form.get("password", "")
        if len(new_password) < 8:
            flash("Use a password with at least eight characters.", "error")
        elif pyotp.TOTP(account["otp_secret"]).verify(request.form.get("otp", ""), valid_window=1):
            with database() as (_, cursor):
                cursor.execute("UPDATE users SET password = %s WHERE student_id = %s", (password_hash.hash(new_password), student_id))
            session.pop("reset_student_id", None)
            flash("Password updated.", "success")
            return redirect(url_for("profile"))
        else:
            flash("That OTP is invalid or expired.", "error")
    return render_template("reset_password.html")


if __name__ == "__main__":
    app.run(debug=True)
