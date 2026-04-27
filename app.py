from flask import Flask, request, jsonify
import uuid
import time # EPOCH, timestamp
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import x

from flask_cors import CORS

from icecream import ic
ic.configureOutput(prefix=f"_____ | ", includeContext=True)

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity # From chatGPT (jwt)

app = Flask(__name__)
CORS(app)  # allows everything

app.config["JWT_SECRET_KEY"] = "super-secret-key" # From chatGPT (jwt)
jwt = JWTManager(app)


############################################################
@app.post("/login")
def login():

    try:
        # TODO: Validate user data
        user_email = x.validate_user_email()
        user_hashed_password = x.validate_user_hashed_password()

        # TODO: Connect to the database
        db, cursor = x.db()
        q = "SELECT user_first_name FROM users WHERE user_email"
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()


        access_token = create_access_token(identity=str(user)),
        return jsonify(access_token=access_token)
        
    
    except Exception as ex:
        ic(ex)
        if "company_exception user_email" in str(ex):
            return "Invalid user_email", 400
        
        if "company_exception user_password" in str(ex):
            return f"Password {x.USER_HASHED_PASSWORD_MIN} to {x.USER_HASHED_PASSWORD_MAX} characters", 400

        # Worst case
        return f"""<browser>System under maintenance</browser>""", 500
        
    finally: 
        if "cursor" in locals(): cursor.close() # Locals refers to anything inside the try or except
        if "db" in locals(): db.close() # db refers to anything inside the database


############################################################
@app.post("/sign-up")
def sign_up():
    try:
        # TODO: Validate user data
        verification_key = x.validate_uuid4()
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()
        user_created_at = int(time.time())
        user_verified_at = 0
        user_forgot_password = 0
        password = x.validate_user_hashed_password()

        # Hasher vores password
        user_hashed_password = generate_password_hash(password)

        ic(user_hashed_password)

        user_pk = uuid.uuid4().hex
        user_verification_key = uuid.uuid4().hex
        ic(user_verification_key)

        # Two times uuid to make it extra secure
        user_reset_password_key = uuid.uuid4().hex + uuid.uuid4().hex
        ic(user_reset_password_key)


        # TODO: Connect to the database
        db, cursor = x.db()

        # TODO: Insert user data to the db
        q = "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(q, (user_pk, user_first_name, user_last_name, user_email, user_hashed_password, user_created_at, user_verified_at, user_verification_key, user_forgot_password, user_reset_password_key))
        db.commit()

        # TODO: Send email with verification key
        html = jsonify(verification_key=verification_key)

        # Pointing to global email function
        x.send_email("Activate your account", html)
        return "Please check your email maybe it arrived in the spam folder"
    
    except Exception as ex:
        ic(ex)
        # If statement for first name
        if "company_exception user_first_name" in str(ex):
            return f"User first name {x.USER_FIRST_NAME_MIN} to {x.USER_FIRST_NAME_MAX} characters", 400
        
        if "company_exception email" in str(ex):
            return "Invalid email", 400
        
        if "company_exception user_hashed_password" in str(ex):
            return f"Password {x.USER_HASHED_PASSWORD_MIN} to {x.USER_HASHED_PASSWORD_MAX} characters", 400

        # Worst case
        return f"""<browser>System under maintenance</browser>""", 500
        
    finally: 
        if "cursor" in locals(): cursor.close() # Locals refers to anything inside the try or except
        if "db" in locals(): db.close() # db refers to anything inside the database


############################################################
@app.get("/verify/<key>")
def verify_account(key):
    try:
        # TODO: Validate key
        validated_key = x.validate_uuid4(key)

        # TODO: Connect to the db
        db, cursor = x.db()

        # TODO: Update the verified_at column
        user_verified_at = int(time.time())

        q = """
            UPDATE users 
            SET user_verified_at = %s 
            WHERE user_verification_key = %s AND user_verified_at = 0
        """

        # TODO: Update the user_verification_key column
        cursor.execute(q, (user_verified_at, validated_key))
        db.commit()
        if cursor.rowcount == 0:
            return "User already verified"

        return f"Welcome to the system, you are verified"
    
    except Exception as ex:
        ic(ex)
        # If statement for first name
        if "company_exception uuid4 invalid" in str(ex):
            return f"""<browser>Invalid key</browser>""", 400

        # Worst case
        return f"""<browser>System under maintenance</browser>""", 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.post("/forgot-password")
def forgot_password():
    try:
        email = x.validate_email(request.form.get("email", ""))
        db, cursor = x.db()
        q = "SELECT user_reset_password_key AS 'key' FROM users WHERE user_email = %s"
        cursor.execute(q, (email,))
        row = cursor.fetchone()

        if not row:
            return "Email not found", 400

        html = jsonify(user_reset_password_key=row["key"])

        # Pointing to global email function
        x.send_email("Reset your password", html)

        # return html
        return "Check your email"
    
    except Exception as ex:
        ic(ex)

        if "company_exception email" in str(ex):
            return "Invalid email", 400

        return str(ex), 500
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.get("/reset-password/<key>")
def show_reset_password(key):
    try:
        # TODO: Validate key
        validated_key = x.validate_uuid4(key)

        # TODO: Connect to the db
        db, cursor = x.db()

        q = """
            SELECT user_reset_password_key FROM users 
            WHERE user_reset_password_key = %s
        """

        # TODO: Update the verification_key column
        cursor.execute(q, (key,))
        row = cursor.fetchone()

        # The user should NEVER see this, so a hacker...
        if not row:
            return "Ups...", 400

        return jsonify(key=key)
    
    except Exception as ex:
        ic(ex)
        # If statement for first name
        if "company_exception user_first_name" in str(ex):
            return f"""<browser>Username not valid</browser>""", 400

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.post("/reset-password")
def reset_password():
    try:
        password = x.validate_user_password(request.form.get("password", ""))
        confirm_password = request.form.get("confirm-password", "").strip()

        # If passwords not match, make a error
        if confirm_password != password:
            return "Password does not match", 400

        # Validate key again
        key = x.validate_uuid4(request.form.get("key", ""))

        # Hash password
        user_forgot_password = generate_password_hash(password)

        # TODO: Connect to the db
        db, cursor = x.db()

        # Update new password
        q = """
            UPDATE users
            SET user_hashed_password = %s 
            WHERE user_reset_password_key = %s
        """

        # TODO: Update the verification_key column
        cursor.execute(q, (user_forgot_password, key))
        db.commit()
        
        return "Password changed, please login"
    
    except Exception as ex:
        ic(ex)
        if "company_exception user_hashed_password" in str(ex):
            return f"Password {x.USER_HASHED_PASSWORD_MIN} to {x.USER_HASHED_PASSWORD_MAX} characters", 400
        
        if "company_exception uuid4 invalid" in str(ex):
            return "Invalid key", 400

        return str(ex), 500
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()




