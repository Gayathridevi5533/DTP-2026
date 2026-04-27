from flask import Flask, request, render_template_string
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clicks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Database config (SQLite)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///clicks.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Model
class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(100))

# Create DB
with app.app_context():
    db.create_all()

# Helper to get real IP
def get_client_ip():
    if request.headers.get("X-Forwarded-For"):
        return request.headers.get("X-Forwarded-For").split(",")[0]
    return request.remote_addr

# Route
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        ip = get_client_ip()
        new_click = Click(ip_address=ip)
        db.session.add(new_click)
        db.session.commit()

    return render_template_string("""
        <h1>Click Tracker</h1>
        <form method="POST">
            <button type="submit">Click me</button>
        </form>
    """)

if __name__ == "__main__":
    app.run(debug=True)