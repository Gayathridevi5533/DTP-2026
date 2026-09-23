from extensions import db, mail
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, date, time
from flask_mail import Message
from flask import request
import secrets
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import (
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
    )
import re
import csv
from io import TextIOWrapper

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

routes = Blueprint("routes", __name__)
from extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))


# =========================
# DATABASE MODEL
# =========================
class Student(UserMixin, db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True
    )

    email = db.Column(
        db.String(120),
        unique=True
    )

    student_code = db.Column(
        db.String(50),
        unique=True
    )

    student_class = db.Column(
        db.String(150),
        unique=False
    )

    password = db.Column(
        db.String(300)
    )

    reset_token = db.Column(
        db.String(200)
    )


class Schedule(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    start_date = db.Column(
        db.Date,
        nullable=False
    )

    end_date = db.Column(
        db.Date,
        nullable=False
    )

    week = db.Column(
        db.String(1),
        nullable=False
    )

    day = db.Column(
        db.String(10),
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    class_code = db.Column(
        db.String(50),
        nullable=False
    )

    teacher = db.Column(
        db.String(50)
    )


class Attendance(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_name = db.Column(db.String(100))

    student_email = db.Column(db.String(120))

    student_code = db.Column(db.String(50))

    student_id = db.Column(db.Integer)

    ip = db.Column(db.String(50))

    latitude = db.Column(db.Float)

    longitude = db.Column(db.Float)

    distance = db.Column(db.Float)

    status = db.Column(
        db.String(50)
     )

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    study_reason = db.Column(
        db.String(300)
    )


# =========================
# SCHOOL LOCATION
# =========================

TARGET_LAT = -43.5075
TARGET_LON = 172.5762

MAX_DISTANCE = 200


# =========================
# DISTANCE FUNCTION
# =========================

def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371000

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# =========================
# HOME PAGE
# =========================

@routes.route("/")
@login_required
def home():

    records = Attendance.query.filter_by(
        student_id=current_user.id
    ).all()

    total_days = len(records)

    present_days = sum(
        1 for record in records
        if record.status == "allowed"
    )

    absent_days = sum(
        1 for record in records
        if record.status == "denied"
    )

    if total_days > 0:
        attendance_percentage = round(
            (present_days / total_days) * 100
        )
    else:
        attendance_percentage = 0

    return render_template(
        "index.html",
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        attendance_percentage=attendance_percentage
    )


# =========================
# VERIFY LOCATION
# =========================

@routes.route("/verify_location", methods=["POST"])
def verify_location():

    data = request.get_json()

    user_lat = data.get("lat")
    user_lon = data.get("lon")

    # user_ip = request.remote_addr

    dist = calculate_distance(
        user_lat,
        user_lon,
        TARGET_LAT,
        TARGET_LON
    )

    if dist <= MAX_DISTANCE:
        status = "denied"
    else:
        status = "allowed"

    # ip = request.remote_addr
    
    return jsonify({
        "status": status,
        "distance": round(dist, 2)
        # "id": attendance_id
})


@routes.route("/check_schedule")
@login_required
def check_schedule():

    now = datetime.now()

    today = now.date()
    current_time = now.time()
    day_name = now.strftime("%A")

    print("Schedule date:", today)
    print("Schedule time:", current_time)
    print("Schedule day:", day_name)

    schedule = Schedule.query.filter(
        Schedule.start_date <= today,
        Schedule.end_date >= today,
        Schedule.day == day_name,
        Schedule.start_time <= current_time,
        Schedule.end_time >= current_time
    ).first()

    if schedule:
        return jsonify({
            "status": "allowed",
            "message": "Attendance is available."
        })

    return jsonify({
        "status": "denied",
        "message": "Attendance is not available at this time."
    })


@routes.route("/submit_reason", methods=["POST"])
@login_required
def submit_reason():

    data = request.get_json()

    user_lat = data.get("lat")
    user_lon = data.get("lon")

    # =========================
    # CHECK LOCATION
    # =========================

    dist = calculate_distance(
        user_lat,
        user_lon,
        TARGET_LAT,
        TARGET_LON
    )

    if dist <= MAX_DISTANCE:
        status = "allowed"
    else:
        status = "denied"

    # =========================
    # CHECK SCHEDULE
    # =========================

    now = datetime.now()

    today = now.date()
    current_time = now.time()

    day_name = now.strftime("%A")

    schedule = Schedule.query.filter(
        Schedule.start_date <= today,
        Schedule.end_date >= today,
        Schedule.day == day_name,
        Schedule.start_time <= current_time,
        Schedule.end_time >= current_time
    ).first()

    # =========================
    # DENY IF NOT SCHEDULED
    # =========================

    if not schedule:

        return jsonify({
            "status": "denied",
            "reason": "schedule",
            "message": "Attendance is not available at this time."
        }), 403

    # =========================
    # DENY IF OUTSIDE SCHOOL
    # =========================

    if status == "denied":

        return jsonify({
            "status": "denied",
            "reason": "location",
            "message": "You are outside the allowed school location."
        }), 403

    # =========================
    # SAVE ATTENDANCE
    # =========================

    ip = request.remote_addr

    study_reason = data.get("study_reason")

    new_attendance = Attendance(

        student_name=current_user.username,

        student_email=current_user.email,

        student_code=current_user.student_code,

        student_id=current_user.id,

        ip=ip,

        latitude=user_lat,

        longitude=user_lon,

        distance=dist,

        status="allowed",

        study_reason=study_reason
    )

    db.session.add(new_attendance)

    db.session.commit()

    return jsonify({
        "status": "allowed",
        "message": "Attendance saved successfully."
    })


@routes.route("/teacher")
def teacher():

    students = Student.query.all()
    records = Attendance.query.all()

    attendance_by_student = {}

    for record in records:
        attendance_by_student[record.student_id] = record

    return render_template(
        "teacher.html",
        students=students,
        attendance_by_student=attendance_by_student
    )

@routes.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":

        username = request.form.get("student_code")

        password = request.form.get("password")

        user = Student.query.filter_by(
            student_code=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            login_user(user)

            return redirect(
                url_for("routes.home")
            )

        else:
            error = "Invalid username or password."

    return render_template("loginpage.html", error=error)


@routes.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("routes.login")
    )


@routes.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        username = request.form.get("username")
        if not re.match(r"^[A-Za-z ]+$", username):
            return "Name must contain letters and spaces only."

        password = request.form.get("password")

        # HASH PASSWORD
        hashed_password = generate_password_hash(password)

        email = request.form.get("email")

        student_code = request.form.get("student_code")

        # CREATE USER
        new_user = Student(

            username=username,

            email=email,

            student_code=student_code,

            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect(url_for("routes.login"))

    return render_template("signup.html")


@routes.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    if request.method == "POST":

        email = request.form.get("email")

        user = Student.query.filter_by(
            email=email
        ).first()

        if user:

            token = secrets.token_hex(16)

            user.reset_token = token

            db.session.commit()

            reset_link = url_for(
                "routes.reset_password",
                token=token,
                _external=True
            )

            msg = Message(
                "Password Reset",
                sender="gayathrideviganesh5533@gmail.com",
                recipients=[email]
            )

            msg.body = f"""
Click the link below to reset your password:

{reset_link}
"""

            mail.send(msg)

            return "Reset email sent!"

        return "No account found"

    return render_template(
        "forgot_password.html"
    )


@routes.route("/test_mail")
def test_mail():

    print("AFTER index:")
    msg = Message(
        subject="Test Email",
        sender="gayathrideviganesh5533@gmail.com",
        recipients=["your_other_email@gmail.com"]
    )

    msg.body = "This is a test email from Flask."

    mail.send(msg)

    return "Email sent!"


@routes.route("/import_students", methods=["GET", "POST"])
def import_students():

    if request.method == "POST":

        file = request.files["csv_file"]

        csv_file = TextIOWrapper(
            file,
            encoding="utf-8"
        )

        reader = csv.DictReader(csv_file)

        imported = 0

        errors = []

        csv_student_codes = set()

        for row_number, row in enumerate(reader, start=2):

            username = row.get(
                "username",
                ""
            ).strip()

            email = row.get(
                "email",
                ""
            ).strip()

            student_code = row.get(
                "student_code",
                ""
            ).strip()

            student_class = row.get(
                "student_class",
                ""
            ).strip()

            # ------------------
            # REQUIRED FIELDS
            # ------------------

            if not username or not email or not student_code or not student_class:

                errors.append(
                    f"Row {row_number}: Missing data."
                )

                continue

            # ------------------
            # EMAIL VALIDATION
            # ------------------

            if not re.match(
                r"^[^@]+@[^@]+\.[^@]+$",
                email
            ):

                errors.append(
                    f"Row {row_number}: Invalid email."
                )

                continue

            # ------------------
            # STUDENT ID
            # ------------------

            if not re.match(
                r"^\d{5}$",
                student_code
            ):

                errors.append(
                    f"Row {row_number}: Student ID must be exactly 5 digits."
                )

                continue

            # ------------------
            # DUPLICATES IN CSV
            # ------------------

            if student_code in csv_student_codes:

                errors.append(
                    f"Row {row_number}: Duplicate student ID in CSV."
                )

                continue

            csv_student_codes.add(
                student_code
            )

            # ------------------
            # DUPLICATES IN DB
            # ------------------

            existing_student = Student.query.filter_by(
                student_code=student_code
            ).first()

            if existing_student:

                errors.append(
                    f"Row {row_number}: Student ID already exists."
                )

                continue

            existing_email = Student.query.filter_by(
                email=email
            ).first()

            if existing_email:

                errors.append(
                    f"Row {row_number}: Email already exists."
                )

                continue

            # ------------------
            # CREATE STUDENT
            # ------------------

            new_student = Student(

                username=username,

                email=email,

                student_code=student_code,

                student_class=student_class,

                password="",

                reset_token=None
            )

            db.session.add(
                new_student
            )

            imported += 1

        db.session.commit()

        return f"""
        Imported: {imported}<br>
        Errors: {len(errors)}<br><br>
        {'<br>'.join(errors)}
        """

    return render_template(
        "import_students.html"
    )


@routes.route(
    "/reset_password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    user = Student.query.filter_by(
        reset_token=token
    ).first()

    if not user:
        return "Invalid token"

    if request.method == "POST":

        new_password = request.form.get(
            "password"
        )

        hashed_password = generate_password_hash(
            new_password
        )

        user.password = hashed_password

        user.reset_token = None

        db.session.commit()

        return redirect(
            url_for("routes.login")
        )

    return render_template(
        "reset_password.html"
    )


@routes.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():

    if request.method == 'POST':

        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        if not check_password_hash(
                current_user.password,
                current_password):
            flash('Current password is incorrect.')
            return redirect(url_for('routes.change_password'))

        current_user.password = generate_password_hash(new_password)

        db.session.commit()

        flash('Password changed successfully.')
        return redirect(url_for('routes.login'))

    return render_template('change_password.html')


@routes.route("/import_schedule", methods=["GET", "POST"])
def import_schedule():

    if request.method == "POST":

        # Delete existing schedule records
        Schedule.query.delete()
        db.session.commit()

        file = request.files["csv_file"]

        csv_file = TextIOWrapper(
            file,
            encoding="utf-8"
        )

        reader = csv.DictReader(csv_file)

        imported = 0
        errors = []

        for row_number, row in enumerate(reader, start=2):

            try:
                # Get values from CSV
                start_date_text = row.get("start_date", "").strip()
                end_date_text = row.get("end_date", "").strip()
                week = row.get("week", "").strip()
                day = row.get("day", "").strip()
                start_time_text = row.get("start_time", "").strip()
                end_time_text = row.get("end_time", "").strip()
                class_code = row.get("class_code", "").strip()
                teacher = row.get("teacher", "").strip()

                # Check required fields
                if (
                    not start_date_text
                    or not end_date_text
                    or not week
                    or not day
                    or not start_time_text
                    or not end_time_text
                    or not class_code
                ):
                    errors.append(
                        f"Row {row_number}: Missing required data."
                    )
                    continue

                # Check week
                if week not in ["A", "B"]:
                    errors.append(
                        f"Row {row_number}: Week must be A or B."
                    )
                    continue

                # Convert dates from CSV strings to Python date objects
                start_date = datetime.strptime(
                    start_date_text,
                    "%Y-%m-%d"
                ).date()

                end_date = datetime.strptime(
                    end_date_text,
                    "%Y-%m-%d"
                ).date()

                # Convert times from CSV strings to Python time objects
                start_time = datetime.strptime(
                    start_time_text,
                    "%H:%M:%S"
                ).time()

                end_time = datetime.strptime(
                    end_time_text,
                    "%H:%M:%S"
                ).time()

                # Create schedule record
                new_schedule = Schedule(
                    start_date=start_date,
                    end_date=end_date,
                    week=week,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    class_code=class_code,
                    teacher=teacher
                )

                db.session.add(new_schedule)

                imported += 1

            except ValueError as e:

                errors.append(
                    f"Row {row_number}: Invalid date or time format. {e}"
                )

        db.session.commit()

        return f"""
        Imported: {imported}<br>
        Errors: {len(errors)}<br><br>
        {'<br>'.join(errors)}
        """

    return render_template("import_schedule.html")