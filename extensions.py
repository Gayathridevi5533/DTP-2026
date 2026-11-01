# import SQLAlchemy to work with the database
from flask_sqlalchemy import SQLAlchemy

# import LoginManager to manage user login sessions
from flask_login import LoginManager

# import Mail to send emails from the website
from flask_mail import Mail


# create the database instance used throughout the project
db = SQLAlchemy()

# create the login manager to handle logged in users
login_manager = LoginManager()

# create the mail instance for sending emails
mail = Mail()
