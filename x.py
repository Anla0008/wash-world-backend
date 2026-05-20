from flask import request, make_response
import mysql.connector
import re # Regular expression module for validating input also called "regex"
from functools import wraps

from icecream import ic
ic.configureOutput(prefix=f"___ | ", includeContext=True)

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
            database = "eksamen_washworld" # Navnet på den database vi har i vores docker (kan skiftes til docker-compose.ylm)
        )
        cursor = db.cursor(dictionary=True)
        return db, cursor
    except Exception as e:
        print(e, flush=True)
        raise Exception("Database under maintenance", 500)


#######################################################################################
#                    HERUNDER BEGYNDER VALIDATION FOR USERS TABEL                     #
#######################################################################################

#------------- VALIDATION FOR FIRST_NAME -------------#
USER_FIRST_NAME_MIN = 2
USER_FIRST_NAME_MAX = 20
REGEX_USER_FIRST_NAME = f"^.{{{USER_FIRST_NAME_MIN},{USER_FIRST_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_first_name():
    user_first_name = request.json.get("user_first_name", "").strip()

    if not re.match(REGEX_USER_FIRST_NAME, user_first_name):
        raise Exception ("company_exception user_first_name")
    return user_first_name

#------------- VALIDATION FOR LAST_NAME -------------#
USER_LAST_NAME_MIN = 2
USER_LAST_NAME_MAX = 20
REGEX_USER_LAST_NAME = f"^.{{{USER_LAST_NAME_MIN},{USER_LAST_NAME_MAX}}}$" # Regex med en f-string.

def validate_user_last_name():
    user_last_name = request.json.get("user_last_name", "").strip()

    if not re.match(REGEX_USER_LAST_NAME, user_last_name):
        raise Exception ("company_exception user_last_name")
    return user_last_name


#-------------- VALIDATION FOR EMAIL ----------------#
# The r prefix makes this a raw string, so backslashes are treated literally.
# This is useful for regex patterns because regex also uses backslashes for special syntax.
REGEX_USER_EMAIL = r"^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$"

def validate_user_email():
    user_email = request.json.get("user_email", "").strip()
    if not re.match(REGEX_USER_EMAIL, user_email):
        raise Exception("company_exception user_email")

    # Bruges nede i "send email" 
    return user_email


#-------------- VALIDATION FOR PASWORD --------------#
USER_HASHED_PASSWORD_MIN = 8
USER_HASHED_PASSWORD_MAX = 255
REGEX_USER_HASHED_PASSWORD = f"^.{{{USER_HASHED_PASSWORD_MIN},{USER_HASHED_PASSWORD_MAX}}}$" # Regex med en f-string.

def validate_user_hashed_password():
    user_hashed_password = request.json.get("user_hashed_password", "").strip()

    if not re.match(REGEX_USER_HASHED_PASSWORD, user_hashed_password):
        raise Exception ("company_exception user_hashed_password")
    return user_hashed_password


#------------ VALIDATION FOR CHECKED PASWORD ------------# !!!!!!!!!!!!!!!!!!!!!
USER_HASHED_PASSWORD_MIN = 8
USER_HASHED_PASSWORD_MAX = 255
REGEX_USER_HASHED_PASSWORD = f"^.{{{USER_HASHED_PASSWORD_MIN},{USER_HASHED_PASSWORD_MAX}}}$" # Regex med en f-string.

def validate_user_checked_hashed_password():
    user_checked_hashed_password = request.json.get("user_checked_hashed_password", "").strip()

    if not re.match(REGEX_USER_HASHED_PASSWORD, user_checked_hashed_password):
        raise Exception ("company_exception user_checked_hashed_password")
    return user_checked_hashed_password


#--------------- VALIDATION FOR UUID ----------------#
# 0 to 9 letters a to f
REGEX_UUID4 = r"^[0-9a-f]{32}$"
def validate_uuid4(uuid4):
    uuid = uuid4.strip()
    if not re.match(REGEX_UUID4, uuid):
        raise Exception("company_exception uuid4 invalid")
    return uuid


#----------- VALIDATION FOR LICENSE_PLATE -----------#
# Dansk format: præcis 2 bogstaver + præcis 5 cifre, fx "AB12345"
REGEX_LICENSE_PLATE = r"^[A-Z]{2}\d{5}$"

def validate_license_plate():
    plate_number = request.json.get("plate_number", "").strip().upper()

    if not re.match(REGEX_LICENSE_PLATE, plate_number):
        raise Exception("company_exception license_plate")
    return plate_number


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


#------------------- SEND DAMAGE REPORT EMAIL ---------------------#
# Tried to match this function with the validate email function
def send_damage_report_email(subject, html):
    try:
        sender_email = "leamhejlskov@gmail.com" # TODO: skift til brugerens email
        password = "sfra rbpr hiao rrlu"

        # Fixed receiver. All damage reports go to this address – should be washworlds service email
        receiver_email = "lamo0004@stud.ek.dk" 

        # Build the email message
        message = MIMEMultipart()
        message["From"] = "Washworld"
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(html, "html"))

        # Connect to Gmail SMTP and send
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message.as_string())
        ic("Damage report email sent!")

        return "email sent"

    except Exception as ex:
        ic(ex)
        return "cannot send email", 500
    finally:
        pass