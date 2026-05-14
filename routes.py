from extensions import db
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import (
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
    )

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

    password = db.Column(
        db.String(300)
    )


# =========================
# DATABASE MODEL
# =========================

class Attendance(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    student_id = db.Column(db.Integer)

    student_name = db.Column(
        db.String(100)
    )

    student_email = db.Column(
        db.String(120)
    )

    ip = db.Column(db.String(50))

    latitude = db.Column(db.Float)

    longitude = db.Column(db.Float)

    distance = db.Column(db.Float)

    status = db.Column(db.String(20))

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

    return render_template("index.html")


# =========================
# VERIFY LOCATION
# =========================

@routes.route("/verify_location", methods=["POST"])
def verify_location():

    data = request.get_json()

    user_lat = data.get("lat")
    user_lon = data.get("lon")

    user_ip = request.remote_addr

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

    ip = request.remote_addr
    
    # SAVE TO DATABASE
    new_attendance = Attendance(

    student_id=current_user.id,

    student_name=current_user.username,

    student_email=current_user.email,

    ip=ip,

    latitude=user_lat,

    longitude=user_lon,

    distance=dist,

    status=status,

    study_reason=study_reason
    )

    db.session.add(new_attendance)
    db.session.commit()
    attendance_id = new_attendance.id

    return jsonify({
    "status": status,
    "distance": round(dist, 2),
    "id": attendance_id
})

@routes.route("/submit_reason", methods=["POST"])
def submit_reason():

    data = request.get_json()

    attendance_id = data.get("id")

    reason = data.get("study_reason")

    record = Attendance.query.get(attendance_id)

    if record:

        record.study_reason = reason

        db.session.commit()

        return jsonify({
            "message": "saved"
        })

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

        password = request.form.get("password")

        # HASH PASSWORD
        hashed_password = generate_password_hash(password)

        email = request.form.get("email")

        # CREATE USER
        new_user = Student(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)

        db.session.commit()

        return redirect(url_for("routes.login"))

    return render_template("signup.html")