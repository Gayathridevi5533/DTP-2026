from flask import Blueprint, request, jsonify, render_template
import math

routes = Blueprint("routes", __name__)

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

    if dist <= MAX_DISTANCE_METERS:
        return jsonify({"status": "allowed", "distance": dist})
    else:
        return jsonify({"status": "denied", "distance": dist})