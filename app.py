"""Main application module for the attendance verification system."""

# Import Flask and the extensions used in the application
from flask import Flask
from extensions import db, login_manager, mail
from routes import routes

# Set up the Flask application
app = Flask(__name__)

# Set the secret key used for sessions
# SECRET KEY
app.config["SECRET_KEY"] = "supersecretkey"

# Email settings used for password reset emails
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False

# Connect Flask-Mail to the app
mail.init_app(app)

# DATABASE
# Set up the SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CONNECT DATABASE
# Initialise the database and login manager
db.init_app(app)
login_manager.init_app(app)

# Send users to the login page if they need to log in
login_manager.login_view = "routes.login"
login_manager.login_message = None

# REGISTER ROUTES
# Make the routes available to the application
app.register_blueprint(routes)

# CREATE TABLES
# Create the database tables if they do not already exist
with app.app_context():
    db.create_all()


# Run the application directly when this file is opened
if __name__ == "__main__":
    app.run(debug=True, port=4040)
