from flask import Blueprint, render_template, request, jsonify
from extensions import db

from math import radians, sin, cos, sqrt, atan2
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify

routes = Blueprint("routes", __name__)

# =========================
# DATABASE MODEL
# =========================

class Attendance(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    ip = db.Column(db.String(100))

    latitude = db.Column(db.Float)

    longitude = db.Column(db.Float)

    distance = db.Column(db.Float)

    status = db.Column(db.String(20))

    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    study_reason = db.Column(db.String(300))


# =========================
# SCHOOL LOCATION
# =========================

TARGET_LAT = -43.508
TARGET_LON = 172.574

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

    # SAVE TO DATABASE
    new_attendance = Attendance(

        ip=user_ip,

        latitude=user_lat,

        longitude=user_lon,

        distance=dist,

        status=status

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