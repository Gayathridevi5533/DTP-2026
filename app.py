from flask import Flask
from extensions import db, login_manager, mail
#from flask_mail import Mail, Message
from routes import routes

app = Flask(__name__)

# SECRET KEY
app.config["SECRET_KEY"] = "supersecretkey"

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USERNAME'] = 'gayathrideviganesh5533@gmail.com'  # Use your actual Gmail address
# app.config['MAIL_PASSWORD'] = 'mypfxfgvoxdnyuxu'     # Use your generated App Password
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USE_SSL'] = False

app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = None
app.config['MAIL_PASSWORD'] = None
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False

mail.init_app(app)

# DATABASE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///attendance.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# CONNECT DATABASE
db.init_app(app)
login_manager.init_app(app)

login_manager.login_view = "routes.login"

# REGISTER ROUTES
app.register_blueprint(routes)

# CREATE TABLES
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True, port=4040)