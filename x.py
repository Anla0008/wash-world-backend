from flask import request, make_response
import mysql.connector
import re # Regular expression module for validating input also called "regex"
from functools import wraps

from icecream import ic
ic.configureOutput(prefix=f"_____ | ", includeContext=True)

# Library to send email
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

########################### CONNECTION TO DATABASE ####################################
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

################################ NO CHACHE IN COOKIES #################################
def no_cache(view):
    @wraps(view)
    def no_cache_view(*args, **kwargs):

        response = make_response(view(*args, **kwargs))
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

        return response
    return no_cache_view


#######################################################################################
#                    HERUNDER BEGYNDER VALIDATION FOR USERS TABEL                     #
#######################################################################################

#------------- VALIDATION FOR FIRST_NAME -------------#
USER_FIRST_NAME_MIN = 2
USER_FIRST_NAME_MAX = 20
REGEX_USER_FIRST_NAME = f"^.{{{USER_FIRST_NAME_MIN},{USER_FIRST_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_first_name():
    user_first_name = request.form.get("user_first_name", "").strip()

    if not re.match(REGEX_USER_FIRST_NAME, user_first_name):
        raise Exception ("company_exception user_first_name")
    return user_first_name

#------------- VALIDATION FOR LAST_NAME -------------#
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
REGEX_USER_LAST_NAME = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_last_name():
    user_last_name = request.form.get("user_last_name", "").strip()

    if not re.match(REGEX_USER_LAST_NAME, user_last_name):
        raise Exception ("company_exception user_last_name")
    return user_last_name


#-------------- VALIDATION FOR EMAIL ----------------#
REGEX_USER_EMAIL = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_user_email():
    user_email = request.form.get("user_email", "").strip()
    if not re.match(REGEX_EMAIL, user_email):
        raise Exception("company_exception user_email")

    # Bruges nede i "send email" 
    return validate_email(user_email)


#-------------- VALIDATION FOR PASWORD --------------#
USER_HASHED_PASSWORD_MIN = 8
USER_HASHED_PASSWORD_MAX = 255
REGEX_USER_HASHED_PASSWORD = f"^.{{{USER_HASHED_PASSWORD_MIN},{USER_HASHED_PASSWORD_MAX}}}$" # Regex med en f-string.

def validate_user_password():
    user_hashed_password = request.form.get("user_hashed_password", "").strip()

    if not re.match(REGEX_USER_HASHED_PASSWORD, user_hashed_password):
        raise Exception ("company_exception user_hashed_password")
    return user_hashed_password


#--------------- VALIDATION FOR UUID ----------------#
# 0 to 9 letters a to f
REGEX_UUID4 = "^[0-9a-f]{32}$"
def validate_uuid4(uuid4):
    uuid = uuid4.strip()
    if not re.match(REGEX_UUID4, uuid):
        raise Exception("company_exception uuid4 invalid")
    return uuid


#------------------- SEND EMAIL ---------------------#
# Function without a route
def send_email(subject, html):
    try:    
        # Create a gmail 
        # Enable (turn on) 2 step verification/factor in the google account manager
        # Visit: https://myaccount.google.com/apppasswords
        # Copy the key :
 
        # Email and password of the sender's Gmail account
        sender_email = "leamhejlskov@gmail.com"
        password = "sfra rbpr hiao rrlu"  # If 2FA is on, use an App Password instead
 
        # Receiver email address (vores egen)
        receiver_email = validate_user_email()
        
        # Create the email message 
        message = MIMEMultipart()
        message["From"] = "Washworld"
        message["To"] = receiver_email
        message["Subject"] = subject
 
        # Body of the email
        # body = f"""<h1>Hi</h1><h2>Hi again</h2>"""
        message.attach(MIMEText(html, "html"))
 
        # Connect to Gmail's SMTP server and send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        ic("Email sent successfully!")
 
        return "email sent"
       
    except Exception as ex:
        return "cannot send email", 500
    finally:
        pass