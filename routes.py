from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
import math
from extensions import db



routes = Blueprint("routes", __name__)

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
    

# 🔹 Change this to your target location (example coords)
TARGET_LAT = -43.5075
TARGET_LON = 172.5762
MAX_DISTANCE_METERS = 200 # allowed radius


def distance(lat1, lon1, lat2, lon2):
    # Haversine formula
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@routes.route("/")
def home():
    return render_template("index.html")


@routes.route("/verify_location", methods=["POST"])
def verify_location():
    data = request.get_json()

    user_lat = data.get("lat")
    user_lon = data.get("lon")

    if user_lat is None or user_lon is None:
        return jsonify({"error": "Missing location"}), 400

    dist = distance(user_lat, user_lon, TARGET_LAT, TARGET_LON)


    status = "allowed" if dist <= MAX_DISTANCE_METERS else "denied"

    # GET USER IP
    ip = request.remote_addr

    # CREATE DATABASE RECORD
    new_attendance = Attendance(
        ip=ip,
        latitude=user_lat,
        longitude=user_lon,
        distance=dist,
        status=status
    )

    # SAVE TO DATABASE
    db.session.add(new_attendance)
    db.session.commit()

    return jsonify({
        "status": status,
        "distance": round(dist, 2)
    })
    
    