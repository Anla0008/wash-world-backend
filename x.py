from flask import request, make_response
import mysql.connector
import re # Regular expression module for validating input also called "regex"
from functools import wraps

from icecream import ic
ic.configureOutput(prefix=f"_____ | ", includeContext=True)

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#-------------CONNECTION TO DATABASE-------------#
def db():
    try:
        db = mysql.connector.connect(
            host = "mariadb",
            user = "root",  
            password = "password",
            database = "2026_1_washworld" # Navnet på den database vi har i vores docker (kan skiftes til docker-compose.ylm)
        )
        cursor = db.cursor(dictionary=True)
        return db, cursor
    except Exception as e:
        print(e, flush=True)
        raise Exception("Database under maintenance", 500)

#-------------NO CACHE COOKIES-------------#
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):

        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response
    return no_cache_view

#-------------VALIDATION FOR NAME-------------#
USER_NAME_MIN = 2
USER_NAME_MAX = 20
REGEX_USER_NAME = f"^.{{{USER_NAME_MIN},{USER_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_name():
    user_name = request.form.get("user_name", "").strip()

    if not re.match(REGEX_USER_NAME, user_name):
        raise Exception ("company_exception user_name")
    return user_name

#-------------VALIDATION FOR LAST NAME-------------#
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
REGEX_USER_LAST_NAME = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_last_name():
    user_last_name = request.form.get("user_last_name", "").strip()

    if not re.match(REGEX_USER_LAST_NAME, user_last_name):
        raise Exception ("company_exception user_last_name")
    return user_last_name

# #------------VALIDATION FOR USER-EMAIL------------#
# #user_email er rette til email så det matcher med forgot-password (ret til hvis det ødelægger de andre funktioner)
# REGEX_USER_EMAIL = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
# def validate_user_email():
#     user_email = request.form.get("user_email", "").strip()
#     if not re.match(REGEX_USER_EMAIL, user_email):
#         raise Exception("company_exception user_email")
#     return user_email

# #------------VALIDATION FOR EMAIL------------#
# #user_email er rette til email så det matcher med forgot-password (ret til hvis det ødelægger de andre funktioner)
# REGEX_USER_EMAIL = "^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"
# def validate_email( email ):
#     email = email.strip()
#    # user_email = request.form.get("user_email", "").strip()
#     if not re.match(REGEX_USER_EMAIL, email):
#         raise Exception("company_exception email")
#     return email


#------------VALIDATION FOR EMAIL------------#
REGEX_EMAIL = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_email(email):
    email = email.strip()
    if not re.match(REGEX_EMAIL, email):
        raise Exception("company_exception email")
    return email

def validate_user_email():
    user_email = request.form.get("user_email", "").strip()
    if not re.match(REGEX_EMAIL, user_email):
        raise Exception("company_exception user_email")
    return validate_email(user_email)

#-------------VALIDATION FOR PASWORD-------------#
USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 255
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$" # Regex med en f-string.

def validate_user_password():
    user_password = request.form.get("user_password", "").strip()

    if not re.match(REGEX_USER_PASSWORD, user_password):
        raise Exception ("company_exception user_password")
    return user_password

#-------------VALIDATION FOR PASWORD-------------#
USER_PASSWORD_MIN = 8
USER_PASSWORD_MAX = 255
REGEX_USER_PASSWORD = f"^.{{{USER_PASSWORD_MIN},{USER_PASSWORD_MAX}}}$" # Regex med en f-string.

def validate_user_password( password ):
    #user_password = request.form.get("user_password", "").strip()
    user_password = password.strip()
    if not re.match(REGEX_USER_PASSWORD, user_password):
        raise Exception ("company_exception user_password")
    return user_password


#-------------VALIDATION FOR UUID-------------#
# 0 to 9 letters a to f
REGEX_UUID4 = "^[0-9a-f]{32}$"
def validate_uuid4(uuid4):
    uuid = uuid4.strip()
    if not re.match(REGEX_UUID4, uuid):
        raise Exception("company_exception uuid4 invalid")
    return uuid

#-------------VALIDATION FOR UUID-------------#
# 0 to 9 letters a to f
REGEX_UUID4_PARANOIA = "^[0-9a-f]{64}$"
def validate_uuid4_paranoia(uuid4):
    uuid = uuid4.strip()
    if not re.match(REGEX_UUID4_PARANOIA, uuid):
        raise Exception("company_exception paranoia")
    return uuid

#------------SEND EMAIL HALLØJ-------------#
def send_email(html):
    try:
        sender_email = "anarikkelarsen@gmail.com"
        password = "ahvp flrb wpoy cdmg"  # If 2FA is on, use an App Password instead

        receiver_email = validate_user_email()

        message = MIMEMultipart()
        message["From"] = f"Washworld <{sender_email}>"
        message["To"] = receiver_email
        message["Subject"] = "Please verify your account"

        message.attach(MIMEText(html, "html"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())

        ic("Email sent successfully")

    except Exception as ex:
        ic(ex)
        return "cannot send email", 500
    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()