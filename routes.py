"""Routes for the Burnside High School Attendance Verification System."""


# import the database, mail and login manager from extensions
from extensions import db, mail, login_manager

# functions needed to calculate the distance between two locations
from math import radians, sin, cos, sqrt, atan2

# used to get the current date and time
from datetime import datetime

# used to create and send emails through Flask
from flask_mail import Message

# request is used to access information sent from the webpage
from flask import request

# used to generate random tokens for password resets
import secrets

# import the Flask functions needed for pages, redirects and messages
from flask import Blueprint, render_template, jsonify, redirect, url_for, flash

# functions used to manage logged in users
from flask_login import (
    UserMixin,
    login_user,
    logout_user,
    login_required,
    current_user
    )

# used for checking and validating text with regular expressions
import re

# used for reading CSV files
import csv

# allows the uploaded CSV file to be read as text
from io import TextIOWrapper


# functions used to hash passwords and check them during login
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# used to keep the teacher access check separate from the actual route
from functools import wraps

# used to return an access denied error
from flask import abort


# create the blueprint for all the routes in this file
routes = Blueprint("routes", __name__)


# SHARED TEACHER LOGIN
# ADMIN CAN CHANGE THESE

# teacher login details used for accessing the teacher dashboard
TEACHER_USERNAME = "teacher@burnside"
TEACHER_PASSWORD = "testpassword"


@login_manager.user_loader
def load_user(user_id):

    """Load a student from the database using their user ID."""

    # check if the logged in account is the teacher
    if user_id == "teacher":
        return Teacher()

    # check if the account belongs to a student
    if user_id.startswith("student:"):

        # get the student id from the user id
        student_id = user_id.split(":", 1)[1]

        # make sure the id contains numbers before searching the database
        if student_id.isdigit():
            return db.session.get(Student, int(student_id))

        # return nothing if the student id is not valid
        return None

    # Support older student sessions
    if user_id.isdigit():
        return db.session.get(Student, int(user_id))

    # return nothing if the user id does not match either account type
    return None


# =========================
# DATABASE MODEL
# =========================

# store student account details in the database
class Student(UserMixin, db.Model):

    # unique id automatically assigned to each student
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # student's full name
    username = db.Column(
        db.String(100),
        unique=True
    )

    # student's email address
    email = db.Column(
        db.String(120),
        unique=True
    )

    # student ID used when logging in
    student_code = db.Column(
        db.String(50),
        unique=True
    )

    # class that the student belongs to
    student_class = db.Column(
        db.String(150),
        unique=False
    )

    # stores the hashed version of the student's password
    password = db.Column(
        db.String(300)
    )

    # stores the token temporarily used for resetting a password
    reset_token = db.Column(
        db.String(200)
    )

    # students are not teacher accounts
    @property
    def is_teacher(self):
        return False

    # return the student id with a prefix to identify student accounts
    def get_id(self):
        return f"student:{self.id}"


# =========================
# SHARED TEACHER USER
# =========================


# create the teacher account separately from the student database
class Teacher(UserMixin):

    # identify the teacher account
    id = "teacher"

    # use the teacher username set above
    username = TEACHER_USERNAME

    # identify the account as a teacher
    role = "teacher"

    # return the teacher id when Flask checks the logged in user
    def get_id(self):
        return "teacher"

    # identify this account as a teacher
    @property
    def is_teacher(self):
        return True


# =========================
# TEACHER-ONLY ACCESS
# =========================


# check whether the logged in user is a teacher before opening a route
def teacher_required(function):

    @wraps(function)
    def decorated_function(*args, **kwargs):

        # stop the request if the user is not a teacher
        if not getattr(current_user, "is_teacher", False):
            abort(403)

        # continue to the original route if the user has teacher access
        return function(*args, **kwargs)

    return decorated_function


# store the attendance schedule information in the database
class Schedule(db.Model):

    # unique id for each schedule record
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # first date that the attendance schedule applies to
    start_date = db.Column(
        db.Date,
        nullable=False
    )

    # last date that the attendance schedule applies to
    end_date = db.Column(
        db.Date,
        nullable=False
    )

    # identify whether the schedule is for week A or week B
    week = db.Column(
        db.String(1),
        nullable=False
    )

    # day of the week when attendance is available
    day = db.Column(
        db.String(10),
        nullable=False
    )

    # time when attendance opens
    start_time = db.Column(
        db.Time,
        nullable=False
    )

    # time when attendance closes
    end_time = db.Column(
        db.Time,
        nullable=False
    )

    # class code for the scheduled session
    class_code = db.Column(
        db.String(50),
        nullable=False
    )

    # teacher responsible for the scheduled session
    teacher = db.Column(
        db.String(50)
    )


# store each student's attendance submission
class Attendance(db.Model):

    # unique id for each attendance record
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # student's name at the time of submission
    student_name = db.Column(db.String(100))

    # student's email address
    student_email = db.Column(db.String(120))

    # student's ID number
    student_code = db.Column(db.String(50))

    # link the attendance record to the student's database id
    student_id = db.Column(db.Integer)

    # IP address recorded when attendance is submitted
    ip = db.Column(db.String(50))

    # latitude of the student's location
    latitude = db.Column(db.Float)

    # longitude of the student's location
    longitude = db.Column(db.Float)

    # distance between the student and the school
    distance = db.Column(db.Float)

    # records whether the attendance was allowed or denied
    status = db.Column(
        db.String(50)
     )

    # automatically record the time when the attendance entry is created
    timestamp = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # reason provided by the student for attending study
    study_reason = db.Column(
        db.String(300)
    )


# =========================
# SCHOOL LOCATION
# =========================

# coordinates of Burnside High School
TARGET_LAT = -43.5075

TARGET_LON = 172.5762

# maximum distance allowed from the school
MAX_DISTANCE = 200


# =========================
# DISTANCE FUNCTION
# =========================


# calculate the distance between the student's location and the school
def calculate_distance(lat1, lon1, lat2, lon2):

    # radius of the Earth in metres
    R = 6371000

    # find the difference between the two latitude and longitude values
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    # use the Haversine formula to calculate the distance
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1))
        * cos(radians(lat2))
        * sin(dlon / 2) ** 2
    )

    # calculate the central angle between the two locations
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # return the distance in metres
    return R * c


# =========================
# HOME PAGE
# =========================


# display the main attendance page after login
@routes.route("/")
@login_required
def home():

    # send teachers directly to their own dashboard
    if getattr(current_user, "is_teacher", False):
        return redirect(url_for("routes.teacher"))

    # get all attendance records belonging to the logged in student
    records = Attendance.query.filter_by(
        student_id=current_user.id
    ).all()

    # count the total number of attendance records
    total_days = len(records)

    # count the records where attendance was allowed
    present_days = sum(
        1 for record in records
        if record.status == "allowed"
    )

    # count the records where attendance was denied
    absent_days = sum(
        1 for record in records
        if record.status == "denied"
    )

    # calculate the attendance percentage if there are records available
    if total_days > 0:

        attendance_percentage = round(
            (present_days / total_days) * 100
        )

    # show 0% when the student has no attendance records yet
    else:
        attendance_percentage = 0

    # send the attendance information to the home page
    return render_template(
        "index.html",
        total_days=total_days,
        present_days=present_days,
        absent_days=absent_days,
        attendance_percentage=attendance_percentage
    )


# =========================
# VERIFY LOCATION
# =========================


# receive the student's location from the webpage
@routes.route("/verify_location", methods=["POST"])
def verify_location():

    # get the location information sent from JavaScript
    data = request.get_json()

    # get the student's latitude and longitude
    user_lat = data.get("lat")

    user_lon = data.get("lon")

    # user_ip = request.remote_addr

    # calculate the distance between the student and the school
    dist = calculate_distance(
        user_lat,
        user_lon,
        TARGET_LAT,
        TARGET_LON
    )

    # check whether the student is within the allowed distance
    if dist <= MAX_DISTANCE:
        status = "allowed"

    # deny the location if the student is too far away
    else:
        status = "denied"

    # ip = request.remote_addr

    # send the result back to the webpage
    return jsonify({
        "status": status,
        "distance": round(dist, 2)
        # "id": attendance_id
    })


# check whether attendance is currently available
@routes.route("/check_schedule")
@login_required
def check_schedule():

    # get the current date and time
    now = datetime.now()

    # separate the date, time and day name
    today = now.date()
    current_time = now.time()
    day_name = now.strftime("%A")

    # print the current details while testing the schedule
    print("Schedule date:", today)
    print("Schedule time:", current_time)
    print("Schedule day:", day_name)

    # find a schedule that matches the current date, day and time
    schedule = Schedule.query.filter(
        Schedule.start_date <= today,
        Schedule.end_date >= today,
        Schedule.day == day_name,
        Schedule.start_time <= current_time,
        Schedule.end_time >= current_time
    ).first()

    # allow attendance if a matching schedule is found
    if schedule:
        return jsonify({
            "status": "allowed",
            "message": "Attendance is available."
        })

    # return a denied response if there is no matching schedule
    return jsonify({
        "status": "denied",
        "message": "Attendance is not available at this time."
    })


# receive the student's reason and save their attendance
@routes.route("/submit_reason", methods=["POST"])
@login_required
def submit_reason():

    # teachers should not be able to submit student attendance
    if getattr(current_user, "is_teacher", False):
        return jsonify({
            "status": "denied",
            "message": "Teachers cannot submit student attendance."
        }), 403

    # get the information sent from the webpage
    data = request.get_json()

    # get the student's current location
    user_lat = data.get("lat")

    user_lon = data.get("lon")

    # =========================
    # CHECK LOCATION
    # =========================

    # calculate how far the student is from school
    dist = calculate_distance(
        user_lat,
        user_lon,
        TARGET_LAT,
        TARGET_LON
    )

    # allow the location if it is within the set distance
    if dist <= MAX_DISTANCE:
        status = "allowed"

    # otherwise deny the location
    else:
        status = "denied"

    # =========================
    # CHECK SCHEDULE
    # =========================

    # get the current date and time
    now = datetime.now()

    # get today's date and the current time separately
    today = now.date()
    current_time = now.time()

    # get the current day name
    day_name = now.strftime("%A")

    # search for a schedule matching today's date, day and time
    schedule = Schedule.query.filter(
        Schedule.start_date <= today,
        Schedule.end_date >= today,
        Schedule.day == day_name,
        Schedule.start_time <= current_time,
        Schedule.end_time >= current_time
    ).first()

    # =========================
    # DENY IF NOT SCHEDULED
    # =========================

    # stop the attendance submission if no schedule is available
    if not schedule:

        return jsonify({
            "status": "denied",
            "reason": "schedule",
            "message": "Attendance is not available at this time."
        }), 403

    # =========================
    # DENY IF OUTSIDE SCHOOL
    # =========================

    # stop the submission if the student is outside the allowed distance
    if status == "denied":

        return jsonify({
            "status": "denied",
            "reason": "location",
            "message": "You are outside the allowed school location."
        }), 403

    # =========================
    # SAVE ATTENDANCE
    # =========================

    # get the IP address of the device making the request
    ip = request.remote_addr

    # get the reason entered by the student
    study_reason = data.get("study_reason")

    # create a new attendance record using the student's details
    new_attendance = Attendance(

        # save the student's name
        student_name=current_user.username,

        # save the student's email
        student_email=current_user.email,

        # save the student's ID
        student_code=current_user.student_code,

        # connect the record to the student's database id
        student_id=current_user.id,

        # save the IP address
        ip=ip,

        # save the location coordinates
        latitude=user_lat,

        longitude=user_lon,

        # save the calculated distance from school
        distance=dist,

        # mark the attendance as allowed
        status="allowed",

        # save the reason entered by the student
        study_reason=study_reason

    )

    # add the new record to the database
    db.session.add(new_attendance)

    # save the changes
    db.session.commit()

    # let the webpage know that attendance was saved
    return jsonify({
        "status": "allowed",
        "message": "Attendance saved successfully."
    })


# display the teacher attendance dashboard
@routes.route("/teacher")
@login_required
@teacher_required
def teacher():

    # get all student accounts from the database
    students = Student.query.all()

    # get all attendance records
    records = Attendance.query.all()

    # create a dictionary to organise attendance by student
    attendance_by_student = {}

    # go through each attendance record
    for record in records:

        # use the student's id to store their attendance record
        attendance_by_student[record.student_id] = record

    # send the student and attendance information to the dashboard
    return render_template(
        "teacher.html",
        students=students,
        attendance_by_student=attendance_by_student
    )


# =========================
# LOGIN
# =========================

# handle both student and teacher login
@routes.route("/login", methods=["GET", "POST"])
def login():

    # store an error message if the login details are incorrect
    error = None

    # check whether the login form has been submitted
    if request.method == "POST":

        # get the selected account type and login details
        account_type = request.form.get("account_type", "student")
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")

        # =========================
        # TEACHER LOGIN
        # =========================

        # check the teacher login separately from student accounts
        if account_type == "teacher":

            # compare the entered details with the teacher login details
            if (
                identifier == TEACHER_USERNAME
                and password == TEACHER_PASSWORD
            ):

                # log the teacher into the system
                login_user(Teacher())

                # open the teacher dashboard
                return redirect(url_for("routes.teacher"))

            # display an error if the teacher details do not match
            error = "Invalid teacher username or password."

        # =========================
        # STUDENT LOGIN
        # =========================

        else:

            # search for a student using either their student ID or email
            user = Student.query.filter(
                db.or_(
                    Student.student_code == identifier,
                    Student.email == identifier
                )
            ).first()

            # check that the account exists and the password is correct
            if (
                user
                and user.password
                and check_password_hash(user.password, password)
            ):

                # log the student into the system
                login_user(user)

                # take the student to their attendance home page
                return redirect(url_for("routes.home"))

            # display an error if the student login details are incorrect
            error = "Invalid Student ID/email or password."

    # display the login page and pass any error message to it
    return render_template(
        "loginpage.html",
        error=error
    )


# log the current user out of the system
@routes.route("/logout")
@login_required
def logout():

    # end the current login session
    logout_user()

    # send the user back to the login page
    return redirect(
        url_for("routes.login")
    )


# =========================
# SIGNUP
# =========================

# allow a new student to create an account
@routes.route("/signup", methods=["GET", "POST"])
def signup():

    # check whether the signup form has been submitted
    if request.method == "POST":

        # get the student's name from the form
        username = request.form.get("username")

        # check that the name only contains letters and spaces
        if not re.match(r"^[A-Za-z ]+$", username):
            return "Name must contain letters and spaces only."

        # get the password entered by the student
        password = request.form.get("password")

        # HASH PASSWORD

        # convert the password into a hashed version before storing it
        hashed_password = generate_password_hash(password)

        # get the student's email address
        email = request.form.get("email")

        # get the student's ID number
        student_code = request.form.get("student_code")

        # CREATE USER

        # create a new student account using the submitted details
        new_user = Student(

            username=username,

            email=email,

            student_code=student_code,

            password=hashed_password
        )

        # add the new account to the database
        db.session.add(new_user)

        # save the new student account
        db.session.commit()

        # take the student to the login page
        return redirect(url_for("routes.login"))

    # show the signup form when the page is first opened
    return render_template("signup.html")


# =========================
# FORGOT PASSWORD
# =========================

# handle password reset requests
@routes.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():

    # check whether the reset form has been submitted
    if request.method == "POST":

        # get the email address entered in the form
        email = request.form.get("email", "").strip()

        # look for a student account with that email address
        user = Student.query.filter_by(email=email).first()

        # Use a general message whether or not the account exists.
        # This avoids revealing which email addresses are registered.
        message_text = (
            "If an account exists for that email, "
            "a password reset link has been sent."
        )

        # only create and send a reset link if the account exists
        if user:

            # generate a random token for the password reset link
            token = secrets.token_hex(16)

            # save the token to the student's database record
            user.reset_token = token

            # save the new token
            db.session.commit()

            # create the password reset link using the token
            reset_link = url_for(
                "routes.reset_password",
                token=token,
                _external=True
            )

            # create the email that will be sent to the student
            msg = Message(
                subject="Password Reset",
                sender="gayathrideviganesh5533@gmail.com",
                recipients=[email]
            )

            # add the reset link to the email
            msg.body = f"""

Click the link below to reset your password:



{reset_link}

"""

            # send the password reset email
            mail.send(msg)

        # return the result to the webpage
        return jsonify({
            "success": True,
            "message": message_text
        })

    # show the forgot password page
    return render_template("forgot_password.html")


# =========================
# TEST EMAIL
# =========================

# route used to check whether email sending is working
@routes.route("/test_mail")
def test_mail():

    # print a message in the terminal when this route is reached
    print("AFTER index:")

    # create a test email
    msg = Message(
        subject="Test Email",
        sender="gayathrideviganesh5533@gmail.com",
        recipients=["your_other_email@gmail.com"]
    )

    # add a simple message to the email
    msg.body = "This is a test email from Flask."

    # send the test email
    mail.send(msg)

    # return a message to confirm that the email was sent
    return "Email sent!"


# =========================
# IMPORT STUDENTS
# =========================

# allow the teacher to upload a CSV file containing student details
@routes.route("/import_students", methods=["GET", "POST"])
@login_required
@teacher_required
def import_students():

    # check whether a CSV file has been submitted
    if request.method == "POST":

        # get the uploaded CSV file
        file = request.files["csv_file"]

        # read the uploaded file using UTF-8 encoding
        csv_file = TextIOWrapper(
            file,
            encoding="utf-8"
        )

        # read the CSV rows using the column headings
        reader = csv.DictReader(csv_file)

        # keep track of how many students have been imported
        imported = 0

        # store any errors found while reading the file
        errors = []

        # keep track of student IDs already seen in this CSV file
        csv_student_codes = set()

        # go through each row in the CSV file
        # start at row 2 because row 1 contains the column headings
        for row_number, row in enumerate(reader, start=2):

            # get the student's name and remove extra spaces
            username = row.get(
                "username",
                ""
            ).strip()

            # get the student's email address
            email = row.get(
                "email",
                ""
            ).strip()

            # get the student's ID number
            student_code = row.get(
                "student_code",
                ""
            ).strip()

            # get the student's class
            student_class = row.get(
                "student_class",
                ""
            ).strip()

            # ------------------
            # REQUIRED FIELDS
            # ------------------

            # make sure all the required columns have been filled in
            if (
                not username
                or not email
                or not student_code
                or not student_class
            ):

                # add an error if any required information is missing
                errors.append(
                    f"Row {row_number}: Missing data."
                )

                # skip this row and continue with the next one
                continue

            # ------------------
            # EMAIL VALIDATION
            # ------------------

            # check whether the email follows the expected format
            if not re.match(
                r"^[^@]+@[^@]+\.[^@]+$",
                email
            ):

                # add an error if the email format is incorrect
                errors.append(
                    f"Row {row_number}: Invalid email."
                )

                # skip this row
                continue

            # ------------------
            # STUDENT ID
            # ------------------

            # student IDs must contain exactly five digits
            if not re.match(
                r"^\d{5}$",
                student_code
            ):

                # add an error if the student ID is not valid
                errors.append(
                    f"Row {row_number}: Student ID must be exactly 5 digits."
                )

                # skip this row
                continue

            # ------------------
            # DUPLICATES IN CSV
            # ------------------

            # check whether this student ID has already appeared in the CSV
            if student_code in csv_student_codes:

                # add an error if the same student ID appears twice
                errors.append(
                    f"Row {row_number}: Duplicate student ID in CSV."
                )

                # skip this row
                continue

            # add the student ID to the set so it can be checked against later rows
            csv_student_codes.add(
                student_code
            )

            # ------------------
            # DUPLICATES IN DB
            # ------------------

            # check whether this student ID already exists in the database
            existing_student = Student.query.filter_by(
                student_code=student_code
            ).first()

            # do not import the student if the ID is already being used
            if existing_student:

                errors.append(
                    f"Row {row_number}: Student ID already exists."
                )

                continue

            # check whether another student is already using this email
            existing_email = Student.query.filter_by(
                email=email
            ).first()

            # do not import the student if the email is already registered
            if existing_email:

                errors.append(
                    f"Row {row_number}: Email already exists."
                )

                continue

            # ------------------
            # CREATE STUDENT
            # ------------------

            # create a new student account using the CSV information
            new_student = Student(

                username=username,

                email=email,

                student_code=student_code,

                student_class=student_class,

                # imported students will set their password through password reset
                password="",

                reset_token=None
            )

            # add the new student to the database session
            db.session.add(
                new_student
            )

            # increase the import count
            imported += 1

        # save all successfully imported students
        db.session.commit()

        # return the number of imported students and any errors
        return f"""
        Imported: {imported}<br>
        Errors: {len(errors)}<br><br>
        {'<br>'.join(errors)}
        """

    # show the CSV upload page
    return render_template(
        "import_students.html"
    )


# =========================
# RESET PASSWORD
# =========================

# open the password reset page using the token from the email
@routes.route(
    "/reset_password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):

    # find the student account that matches the reset token
    user = Student.query.filter_by(
        reset_token=token
    ).first()

    # stop the process if the token does not match any account
    if not user:
        return "Invalid token"

    # check whether the new password has been submitted
    if request.method == "POST":

        # get the new password from the form
        new_password = request.form.get(
            "password"
        )

        # hash the new password before storing it
        hashed_password = generate_password_hash(
            new_password
        )

        # replace the old password with the new hashed password
        user.password = hashed_password

        # clear the reset token so it cannot be used again
        user.reset_token = None

        # save the password change in the database
        db.session.commit()

        # return the student to the login page
        return redirect(
            url_for("routes.login")
        )

    # show the reset password form
    return render_template(
        "reset_password.html"
    )


# =========================
# CHANGE PASSWORD
# =========================

# allow a logged in student to change their password
@routes.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():

    # teachers cannot use the student password change page
    if getattr(current_user, "is_teacher", False):

        flash("The teacher password can only be changed by the administrator.")

        return redirect(url_for("routes.teacher"))

    # check whether the change password form has been submitted
    if request.method == 'POST':

        # get the current and new passwords from the form
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')

        # check whether the entered current password is correct
        if not check_password_hash(
                current_user.password,
                current_password):

            # display an error if the current password is incorrect
            flash('Current password is incorrect.')

            # return to the change password page
            return redirect(url_for('routes.change_password'))

        # hash the new password before saving it
        current_user.password = generate_password_hash(new_password)

        # save the updated password
        db.session.commit()

        # let the student know that the password was changed
        flash('Password changed successfully.')

        # send the student back to the login page
        return redirect(url_for('routes.login'))

    # show the change password form
    return render_template('change_password.html')


# =========================
# IMPORT SCHEDULE
# =========================

# allow the teacher to upload the attendance schedule using a CSV file
@routes.route("/import_schedule", methods=["GET", "POST"])
@login_required
@teacher_required
def import_schedule():

    # check whether a schedule file has been submitted
    if request.method == "POST":

        # Delete existing schedule records
        Schedule.query.delete()
        db.session.commit()

        # get the uploaded CSV file
        file = request.files["csv_file"]

        # read the file using UTF-8 encoding
        csv_file = TextIOWrapper(
            file,
            encoding="utf-8"
        )

        # read the CSV file using its column headings
        reader = csv.DictReader(csv_file)

        # count the number of successfully imported schedules
        imported = 0

        # store errors found in the uploaded file
        errors = []

        # go through each row in the CSV file
        for row_number, row in enumerate(reader, start=2):

            try:

                # Get values from CSV

                # get each schedule value from the current CSV row
                start_date_text = row.get("start_date", "").strip()
                end_date_text = row.get("end_date", "").strip()
                week = row.get("week", "").strip()
                day = row.get("day", "").strip()
                start_time_text = row.get("start_time", "").strip()
                end_time_text = row.get("end_time", "").strip()
                class_code = row.get("class_code", "").strip()
                teacher = row.get("teacher", "").strip()

                # Check required fields

                # make sure all required schedule information is present
                if (
                    not start_date_text
                    or not end_date_text
                    or not week
                    or not day
                    or not start_time_text
                    or not end_time_text
                    or not class_code
                ):

                    # report the row if any required information is missing
                    errors.append(
                        f"Row {row_number}: Missing required data."
                    )

                    # move on to the next row
                    continue

                # Check week

                # only allow week A or week B
                if week not in ["A", "B"]:

                    errors.append(
                        f"Row {row_number}: Week must be A or B."
                    )

                    continue

                # Convert dates from CSV strings to Python date objects

                # convert the start date into a date object
                start_date = datetime.strptime(
                    start_date_text,
                    "%Y-%m-%d"
                ).date()

                # convert the end date into a date object
                end_date = datetime.strptime(
                    end_date_text,
                    "%Y-%m-%d"
                ).date()

                # Convert times from CSV strings to Python time objects

                # convert the starting time into a time object
                start_time = datetime.strptime(
                    start_time_text,
                    "%H:%M:%S"
                ).time()

                # convert the ending time into a time object
                end_time = datetime.strptime(
                    end_time_text,
                    "%H:%M:%S"
                ).time()

                # Create schedule record

                # create a new schedule using the information from the CSV row
                new_schedule = Schedule(
                    start_date=start_date,
                    end_date=end_date,
                    week=week,
                    day=day,
                    start_time=start_time,
                    end_time=end_time,
                    class_code=class_code,
                    teacher=teacher
                )

                # add the schedule to the database
                db.session.add(new_schedule)

                # increase the number of successfully imported schedules
                imported += 1

            # catch errors caused by invalid date or time formats
            except ValueError as e:

                # record which row contains the incorrect information
                errors.append(
                    f"Row {row_number}: Invalid date or time format. {e}"
                )

        # save all the imported schedule records
        db.session.commit()

        # return the import count and any errors
        return f"""
        Imported: {imported}<br>
        Errors: {len(errors)}<br><br>
        {'<br>'.join(errors)}
        """

    # show the schedule upload page
    return render_template("import_schedule.html")


# =========================
# ERROR PAGES
# =========================

# display the custom page when a page cannot be found
@routes.app_errorhandler(404)
def page_not_found(error):

    # show the 404 error page and return the correct status code
    return render_template("404.html"), 404


# display the custom page when an internal server error occurs
@routes.app_errorhandler(500)
def internal_server_error(error):

    # undo any unfinished database changes after the error
    db.session.rollback()

    # show the 500 error page
    return render_template("500.html"), 500


# display the custom page for an unsupported HTTP version
@routes.app_errorhandler(505)
def http_version_not_supported(error):

    # show the 505 error page
    return render_template("505.html"), 505


# =========================
# BLOCK MOBILE DEVICES
# =========================

# check the device making a request before loading the page
@routes.before_request
def block_mobile_devices():

    # get the browser's user agent information
    user_agent = request.headers.get("User-Agent", "").lower()

    # list of words used to identify mobile devices
    mobile_keywords = [

        "android",

        "iphone",

        "ipad",

        "ipod",

        "mobile"

    ]

    # check whether any of the mobile keywords appear in the user agent
    if any(keyword in user_agent for keyword in mobile_keywords):

        # display the blocked device page instead of loading the requested page
        return render_template("device_blocked.html"), 403