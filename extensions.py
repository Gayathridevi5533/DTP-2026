from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

# DATABASE

db = SQLAlchemy()

# LOGIN MANAGER

login_manager = LoginManager()
login_manager.login_view = "routes.login"