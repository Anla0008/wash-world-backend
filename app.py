# from flask import Flask, render_template, request, jsonify
# import uuid
# import time
# import x

# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

# from flask_cors import CORS # husk altid, ellers viker fetch ikke (plus linje 11)

# from icecream import ic
# ic.configureOutput(prefix=f"_____ | ", includeContext=True)

# app = Flask(__name__)
# CORS(app)  # allows everything


# ##############################
# @app.get("/")
# def index():
#     return jsonify({"status":"ok", "message":"Connected"})


# ##############################
# @app.route("/people")
# def get_people():
#     return jsonify({
#         "people": [
#             {"first_name": "Bobby", "last_name": "Bosse", "cpr": "- 12345678"},
#             {"first_name": "Tommy", "last_name": "Hansen", "cpr": "- 87654321"}
#         ]
#     })   

# ##############################
# @app.get("/sign-up")
# def sign_up():
#     return render_template("page_signup.html", x=x)


# ##############################
# @app.post("/api-sign-up")
# def api_sign_up():
#     try:
#         # ToDo: Validate user data
#         user_pk = uuid.uuid4().hex
#         user_name = x.validate_user_name()
#         user_email = x.validate_user_email()
#         user_password = x.validate_user_password()

#         #email = x.validate_email(request.for.get("email", ""))

#         verification_key = uuid.uuid4().hex
#         ic(verification_key)

#         user_reset_password_key = uuid.uuid4().hex + uuid.uuid4().hex   
#         ic(user_reset_password_key)


#         # ToDo: Connect to the database
#         db, cursor = x.db()
#         q = "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s)"
#         cursor.execute(q, (user_pk, user_name, user_email, user_password, verification_key, 0, user_reset_password_key)) # 0 fordi brugern ikke er verified endnu
#         db.commit()
        
#         # ToDo: Insert user data to the database
#         # ToDo: Send email with verfication key

#         html = render_template("email_welcome.html", verification_key=verification_key, user_name=user_name
# )
        
#         send_email(html)
#         # return f"""
#         #         <browser mix-redirect="/login"></browser>"""

#     except Exception as ex:
#         ic(ex)
#         return str(ex), 500
    
#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()
    
# ##############################
# def send_email(html):
#     try:    
#         # Create a gmail 
#         # Enable (turn on) 2 step verification/factor in the google account manager
#         # Visit: https://myaccount.google.com/apppasswords
#         # Copy the key :
 
#         # Email and password of the sender's Gmail account
#         sender_email = "anarikkelarsen@gmail.com"
#         password = "ahvp flrb wpoy cdmg"  # If 2FA is on, use an App Password instead
 
#         # Receiver email address
#         receiver_email = x.validate_user_email()
        
#         # Create the email message
#         message = MIMEMultipart()
#         message["From"] = "Washworld"
#         message["To"] = receiver_email
#         message["Subject"] = "Please verify your account"
 
#         # Body of the email
#         #body = f"""<h1>Hi</h1><h2>Hi again</h2>"""
#         message.attach(MIMEText(html, "html")) #sender html og rendere som html
 
#         # Connect to Gmail's SMTP server and send the email
#         with smtplib.SMTP("smtp.gmail.com", 587) as server:
#             server.starttls()  # Upgrade the connection to secure
#             server.login(sender_email, password)
#             server.sendmail(sender_email, receiver_email, message.as_string())
#         print("Email sent successfully!")
 
#         return "email sent"
       
#     except Exception as ex:
#         return "cannot send email", 500
#     finally:
#         pass


# ##############################
# @app.get("/verify/<key>")
# def verify_account(key):
#     try:
#         key = x.validate_uuid4(key)
#         db, cursor = x.db()
#         user_verified_at = int(time.time())
#         q = """
#             UPDATE users
#             SET user_verified_at = %s
#             WHERE user_verification_key = %s AND user_verified_at = 0
#         """
#         cursor.execute(q, (user_verified_at, key))
#         db.commit()
#         if cursor.rowcount == 0:
#             return "user already verified"

#         return f"Welcome to the system, you are verified"
#     except Exception as ex: 
#         ic(ex)
#         if "company_exception uuid4 invalid" in str(ex):
#             return "Invalid key", 400

#         return str(ex), 500
#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()   

# ##############################
# """
# @app.route ("/forgot-password", methods=["GET", "POST"])
# def show_forgot_password():
#     if request.method == "GET":
#         return render_template("page_forgot_password.html")
#     if request.method == "POST":
# """
# ##############################
# @app.get("/forgot-password")
# def show_forgot_password():
#     return render_template ("page_forgot_password.html")

# ##############################
# @app.post("/forgot-password")
# def forgot_password():
#     try:
#         email = x.validate_email( request.form.get("email", ""))
#         return "Check your email"
 

#     except Exception as ex:
#         ic(ex)
#         if "company_exception email" in str(ex):
#             return "Invalid email", 400
        
#         return str(ex), 500

#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()  


from flask import Flask, render_template, request, jsonify, redirect
import uuid
import time
import x

from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask_cors import CORS

from icecream import ic
ic.configureOutput(prefix=f"_____ | ", includeContext=True)

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, get_jwt


app = Flask(__name__)
CORS(app)

app.config["JWT_SECRET_KEY"] = "your-secret-key"
jwt = JWTManager(app)


##############################
@app.get("/login")
def show_login():
    return render_template("page_login.html", x=x)


##############################
# @app.post("/login")
# def login():
#     try:
#         user_email = x.validate_user_email()
#         user_password = x.validate_user_password(request.form.get("user_password", ""))
        
#         db, cursor = x.db()

#         q = """
#             SELECT * FROM users WHERE user_email = %s AND user_password = %s
#         """

#         cursor.execute(q, (user_email, user_password))
#         user = cursor.fetchone()

#         if not user:
#             raise Exception("company_exception invalid_login")

#         access_token = create_access_token(identity=str(user))

#         return jsonify(access_token=access_token)

#     except Exception as ex:
#         ic(ex)

#         if "company_exception invalid_login" in str(ex):
#             return "Invalid email or password", 400

#         if "company_exception user_email" in str(ex):
#             return "Invalid email format", 400

#         if "company_exception user_password" in str(ex):
#             return f"Password {x.USER_PASSWORD_MIN} to {x.USER_PASSWORD_MAX} characters", 400

#         return str(ex), 500

#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()

@app.post("/login")
def login():
    try:
        user_email = x.validate_user_email()
        user_password = x.validate_user_password(request.form.get("user_password", ""))

        db, cursor = x.db()

        q = """
            SELECT * FROM users WHERE user_email = %s
        """
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()

        if not user:
            raise Exception("company_exception invalid_login")

        password_is_correct = check_password_hash(user["user_password"], user_password)

        if not password_is_correct:
            raise Exception("company_exception invalid_login")

        access_token = create_access_token(identity=str(user))

        return jsonify(access_token=access_token)

    except Exception as ex:
        ic(ex)

        if "company_exception invalid_login" in str(ex):
            return "Invalid email or password", 400

        if "company_exception user_email" in str(ex):
            return "Invalid email format", 400

        if "company_exception user_password" in str(ex):
            return f"Password {x.USER_PASSWORD_MIN} to {x.USER_PASSWORD_MAX} characters", 400

        return str(ex), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

##############################
@app.get("/profile")
@jwt_required()
def show_profile():
    return "profile"



##############################
@app.route("/people")
def get_people():
    return jsonify({
        "people": [
            {"first_name": "Bobby", "last_name": "Bosse", "cpr": "- 12345678"},
            {"first_name": "Tommy", "last_name": "Hansen", "cpr": "- 87654321"}
        ]
    })


##############################
@app.get("/sign-up")
def sign_up():
    return render_template("page_signup.html", x=x)


##############################
@app.post("/api-sign-up")
def api_sign_up():
    try:
        # Validate user data
        user_pk = uuid.uuid4().hex
        user_name = x.validate_user_name()
        user_email = x.validate_user_email()
        user_password = x.validate_user_password(request.form.get("user_password", ""))

        user_hashed_password = generate_password_hash(user_password)


        verification_key = uuid.uuid4().hex
        ic(verification_key)

        user_reset_password_key = uuid.uuid4().hex + uuid.uuid4().hex
        ic(user_reset_password_key)

        # Connect to database
        db, cursor = x.db()

        q = """
            INSERT INTO users
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            q,
            (
                user_pk,
                user_name,
                user_email,
                user_hashed_password,
                verification_key,
                0,
                user_reset_password_key
            )
        )
        db.commit()

        # Render email template
        html = render_template(
            "email_welcome.html",
            verification_key=verification_key,
            user_name=user_name
        )

        # Send verification email
        x.send_email(html)

        return "Check yout email"

    except Exception as ex:
        ic(ex)
        if "company_exception user_name" in str(ex):
            return f"username must be {x.USER_NAME_MIN} to {x.USER_NAME_MAX} characters", 400
        
        if "company_exception user_email" in str(ex):
            return "invalid email", 400
        
        return str(ex), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
@app.get("/verify/<key>")
def verify_account(key):
    try:
        ic(key)
        key = x.validate_uuid4(key)

        db, cursor = x.db()
        user_verified_at = int(time.time())

        q = """
            UPDATE users
            SET user_verified_at = %s
            WHERE user_verification_key = %s AND user_verified_at = 0
        """
        cursor.execute(q, (user_verified_at, key))
        db.commit()

        if cursor.rowcount == 0:
            return "user already verified"

        return redirect ("/login")

    except Exception as ex:
        ic(ex)

        if "company_exception uuid4 invalid" in str(ex):
            return "Invalid key", 400

        return str(ex), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
@app.get("/forgot-password")
def show_forgot_password():
    return render_template("page_forgot_password.html", x=x)


##############################
@app.post("/forgot-password")
def forgot_password():
    try:
        email = x.validate_user_email()
        db, cursor = x.db()
        q = "SELECT user_reset_password_key AS 'key' FROM users WHERE user_email = %s"
        cursor.execute(q, (email,))
        row = cursor.fetchone()

        if not row:
            return "Email not found", 400

        html = render_template("email_forgot_password.html", user_reset_password_key=row["key"])

        x.send_email(html)
        return "check your email", 200


    except Exception as ex:
        ic(ex)
        if "company_exception email" in str(ex):
            return "Invalid email", 400

        return str(ex), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()


##############################
@app.get("/reset-password/<key>")
def show_reset_password(key):
    try:
        key = x.validate_uuid4_paranoia(key)

        db, cursor = x.db()

        q = """
            SELECT user_reset_password_key FROM users WHERE user_reset_password_key = %s
        """
        cursor.execute(q, (key,))
        row= cursor.fetchone()

        if not row:
            return "ups...", 400

        return render_template("page_reset_password.html", key=key)

    except Exception as ex:
        ic(ex)

        if "company_exception uuid4 invalid" in str(ex):
            return "Invalid key", 400

        return str(ex), 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

##############################
@app.post("/reset-password")
def reset_password():
    try:
        password = x.validate_user_password(request.form.get("password", ""))

        confirm_password = request.form.get("confirm-password", "").strip()

        if confirm_password != password:
            return "Password do not match", 400

        key = x.validate_uuid4_paranoia( request.form.get("key") )


        return redirect ("/login")

    except Exception as ex:
        ic(ex)

        if "company_exception user_password" in str(ex):
            return f"Password {x.USER_PASSWORD_MIN} to {x.USER_PASSWORD_MAX} characters", 400

        if "company_exception paranoia" in str(ex):
            return "Invalid key", 400

        return str(ex), 500

    finally:
        if "cursor" in locals():cursor.close()
        if "db" in locals(): db.close()
