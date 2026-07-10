from extensions import db, mail
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from flask_mail import Message
import secrets
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import (
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
    )
import re

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

routes = Blueprint("routes", __name__)
from extensions import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Student.query.get(int(user_id))




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

    password = db.Column(
        db.String(300)
    )

    reset_token = db.Column(
    db.String(200)
    )


# =========================
# DATABASE MODEL
# =========================

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
def home():

    return render_template("index.html")


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

@routes.route("/submit_reason", methods=["POST"])
def submit_reason():

    data = request.get_json()

    user_lat = data.get("lat")
    user_lon = data.get("lon")

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

        status=status,

        study_reason=study_reason
    )

    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({
        "message": "saved"
    })

    db.session.add(new_attendance)
    db.session.commit()
    attendance_id = new_attendance.id    
    return jsonify({
         "message": "not found"
    })

@routes.route("/teacher")
def teacher():

    records = Attendance.query.all()

    return render_template(
        "teacher.html",
        records=records
    )

@routes.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username")

        password = request.form.get("password")

        user = Student.query.filter_by(
            username=username
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            login_user(user)

            return redirect(
                url_for("routes.home")
            )

    return render_template("login.html")


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