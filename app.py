from flask import Flask
from extensions import db
from routes import routes

app = Flask(__name__)

# DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CONNECT DATABASE
db.init_app(app)

# REGISTER ROUTES
app.register_blueprint(routes)

# CREATE TABLES
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=4040)