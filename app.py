from flask import Flask, request, jsonify, redirect
import uuid
import time # EPOCH, timestamp
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import x

from flask_cors import CORS

from icecream import ic
ic.configureOutput(prefix=f"___ | ", includeContext=True)

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity # From chatGPT (jwt)

app = Flask(__name__)
CORS(app)  # allows everything

app.config["JWT_SECRET_KEY"] = "super-secret-key" # From chatGPT (jwt)
jwt = JWTManager(app)


############################################################
@app.post("/sign-up")
def sign_up():
    try:

        ic(request.json)

        # TODO: Validate user data
        # verification_key = x.validate_uuid4()
        verification_key = uuid.uuid4().hex
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

        user_deleted_at = 0
       
       # Two times uuid to make it extra secure
        user_reset_password_key = uuid.uuid4().hex
        ic(user_reset_password_key)

        # Valider nummerplade fra step 2
        plate_number = x.validate_license_plate()
        license_plate_pk = uuid.uuid4().hex

        # TODO: Connect to the database
        db, cursor = x.db()

        # Insert bruger
         # TODO: Insert user data to the db
        q = "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(q, (user_pk, user_first_name, user_last_name, user_email, user_hashed_password, user_created_at, user_verified_at, user_verification_key, user_forgot_password, user_reset_password_key, user_deleted_at))

        # Insert nummerplade med reference til brugeren
        q2 = "INSERT INTO license_plate VALUES (%s, %s, %s)"
        cursor.execute(q2, (license_plate_pk, user_pk, plate_number))

        db.commit()  # Begge inserts committes samlet

        # TODO: Send email with verification key (5000, da flask opdaterer DB og viser tekst)
        html = f"""
            <h1>Velkommen til Washworld!</h1>
            <p>Klik på linket herunder for at aktivere din konto:</p>
            <a href="http://localhost:3000/verify/{user_verification_key}">Aktiver konto</a>
        """

        x.send_email("Aktiver din konto", html)
        return jsonify({"message": "Please check your email maybe it arrived in the spam folder"}), 201
    
    except Exception as ex:
        ic(ex)
        # If statement for first name
        if "company_exception user_first_name" in str(ex):
            return f"User first name {x.USER_FIRST_NAME_MIN} to {x.USER_FIRST_NAME_MAX} characters", 400
        
        if "company_exception email" in str(ex):
            return "Invalid email", 400
        
        if "company_exception user_hashed_password" in str(ex):
            return f"Password {x.USER_HASHED_PASSWORD_MIN} to {x.USER_HASHED_PASSWORD_MAX} characters", 400
        
        # Dublikeret email 
        if "1062" in str(ex):
            return jsonify(error="Email already in use"), 400

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

        return jsonify({"message": "User verified"}), 200
    
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
@app.post("/")
def login():

    try:
        # TODO: Validate user data
        user_email = x.validate_user_email()
        password = x.validate_user_hashed_password()

        # TODO: Connect to the database
        db, cursor = x.db()
        q = "SELECT * FROM users WHERE user_email = %s"
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()

        # Tjek at brugeren findes og at password matcher
        if not user or not check_password_hash(user["user_hashed_password"], password):
            return jsonify(error="Invalid email or password"), 401

        # Create JWT token
        access_token = create_access_token(identity=user["user_pk"])
        return jsonify(access_token=access_token), 200
        
    
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
@app.post("/forgot-password")
def forgot_password():
    try:
        email = x.validate_user_email(request.form.get("email", ""))
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


############################################################
# HVAD VIL VI MED DENNE ?????????????????????
@app.get("/users/<user_pk>")
def get_user(user_pk):
    db, cursor = x.db() 

    cursor.execute("SELECT * FROM users WHERE user_pk = %s", (user_pk,))
    user = cursor.fetchone()

    cursor.close()
    db.close()

    return {"user": user} #Dette er en dictionary


############################################################
@app.delete("/users/<user_pk>")
def delete_user(user_pk):
    try:
        db, cursor = x.db()

        # Slet relaterede data først
        cursor.execute("DELETE FROM feedback WHERE user_fk = %s", (user_pk,))
        cursor.execute("DELETE FROM favorites WHERE user_fk = %s", (user_pk,))
        cursor.execute("DELETE FROM license_plate WHERE user_fk = %s", (user_pk,))

        # Slet så brugeren
        cursor.execute("DELETE FROM users WHERE user_pk = %s", (user_pk,))
        db.commit()

        if cursor.rowcount == 0:
            return {"error": "User not found"}, 404

        return {"error": "User deleted"}, 200

    except Exception as ex:
        ic(ex)
        return {"error": "System under maintenance"}, 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
# @app.get("/locations")
# def get_locations():
#     try:
#         db, cursor = x.db()

#         q = "SELECT * FROM car_wash_locations"
#         cursor.execute(q)
#         locations = cursor.fetchall()

#         if not locations:
#             return jsonify(error="No locations found"), 404

#         return jsonify(locations=locations)

#     except Exception as ex:
#         ic(ex)
#         return jsonify(error="System under maintenance"), 500

#     finally:
#         if "cursor" in locals(): cursor.close()
#         if "db" in locals(): db.close()

@app.get("/locations")
def get_locations():
    try:
        db, cursor = x.db()

        q = """
            SELECT 
                car_wash_locations.*,
                COUNT(car_wash_hall_info.car_wash_pk) AS car_wash_hall_number
            FROM car_wash_locations
            LEFT JOIN car_wash_hall_info
                ON car_wash_locations.location_pk = car_wash_hall_info.car_wash_location_fk
            GROUP BY car_wash_locations.location_pk
        """

        cursor.execute(q)
        locations = cursor.fetchall()

        if not locations:
            return jsonify(error="No locations found"), 404

        return jsonify(locations=locations)

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

############################################################
@app.patch("/profile-information/<user_pk>")
def profile_information(user_pk):
    try:
        # Validerer user information
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()

        # Connect til database
        db, cursor = x.db()

        q = """
            UPDATE users
            SET user_first_name = %s,
                user_last_name = %s,
                user_email = %s
            WHERE user_pk = %s
        """

        cursor.execute(q, (user_first_name, user_last_name, user_email, user_pk))
        db.commit()

        # cursor.rowcount er et tal der fortæller hvor mange rækker der blev påvirket 
        if cursor.rowcount == 0:
            return jsonify(error="User not found"), 404
            
        return jsonify(error="Profile updated"), 200

    except Exception as ex:
        ic(ex)
        return {"error": "System under maintenance"}, 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.post("/feedback")
def feedback():
    try:
        data = request.get_json()
        rating = data.get("rating")
        comment = data.get("comment")
        feedback_pk = uuid.uuid4().hex
        created_at = int(time.time())
    
        # Skal disse måske valideres med x-fil?
        user_fk = 2 #TODO - get the user, that are logged in (with jwt?)
        car_wash_location_fk = 2 #TODO - get the location from the frontend 

        db, cursor = x.db()

        q = """INSERT INTO feedback 
       (feedback_pk, rating, comment, created_at, user_fk, car_wash_location_fk) 
       VALUES (%s, %s, %s, %s, %s, %s)"""
        cursor.execute(q, (feedback_pk, rating, comment, created_at, user_fk, car_wash_location_fk))

        db.commit()

        return jsonify(
            message="Feedback sent successfully"
        ), 201

    except Exception as ex:
        ic(ex)

        return jsonify(
            error="System under maintenance"
        ), 500

    finally:
        if "cursor" in locals():cursor.close()
        if "db" in locals():db.close()


##############################################  
@app.get("/locations/<location_pk>")
def get_single_location(location_pk):
    try:
        db, cursor = x.db()

        q = """
            SELECT 
                car_wash_locations.*,
                COUNT(car_wash_hall_info.car_wash_pk) AS car_wash_hall_number
            FROM car_wash_locations
            LEFT JOIN car_wash_hall_info
                ON car_wash_locations.location_pk = car_wash_hall_info.car_wash_location_fk
            WHERE car_wash_locations.location_pk = %s
            GROUP BY car_wash_locations.location_pk
        """

        cursor.execute(q, (location_pk,))
        location = cursor.fetchone()

        if not location:
            return jsonify(error="Location not found"), 404

        return jsonify(location=location)

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

#######################################################################################
#                           INFO RELATING WASH-PROCESS                                #
#######################################################################################

##############################################
@app.get("/car-wash-history/<user_pk>")
def get_car_wash_history(user_pk):
    try:
        db, cursor = x.db()

        q = "SELECT * FROM car_wash_history WHERE user_fk = %s"
        cursor.execute(q, (user_pk,))
        car_wash_history = cursor.fetchall()

        if not car_wash_history:
            return jsonify(error="No wash history found"), 404

        return jsonify(car_wash_history=car_wash_history)

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


############################################################
@app.post("/car-wash-history")
@jwt_required()
def add_car_wash_history():
    try:
        data = request.get_json()

        car_wash_history_pk = uuid.uuid4().hex

        # Fra frontend
        license_plate_fk = data.get("license_plate_fk")
        car_wash_location_fk = data.get("car_wash_location_fk")
        car_wash_hall_fk = data.get("car_wash_hall_fk")

        # Fra JWT
        user_fk = get_jwt_identity()

        date_of_wash = int(time.time())

        car_wash_price = data.get("car_wash_price")
        car_wash_type = data.get("car_wash_type")
        car_wash_started_at = data.get("car_wash_started_at")
        car_wash_ended_at = data.get("car_wash_ended_at")

        db, cursor = x.db()

        q = """
        INSERT INTO car_wash_history
        (
            car_wash_history_pk,
            license_plate_fk,
            car_wash_location_fk,
            car_wash_hall_fk,
            user_fk,
            date_of_wash,
            car_wash_price,
            car_wash_type,
            car_wash_started_at,
            car_wash_ended_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        cursor.execute(q, (
            car_wash_history_pk,
            license_plate_fk,
            car_wash_location_fk,
            car_wash_hall_fk,
            user_fk,
            date_of_wash,
            car_wash_price,
            car_wash_type,
            car_wash_started_at,
            car_wash_ended_at
        ))

        db.commit()

        return jsonify(message="Car wash history added"), 201

    except Exception as ex:
        ic(ex)
        return jsonify(error=str(ex)), 500

    finally:
        if "cursor" in locals():
            cursor.close()

        if "db" in locals():
            db.close()

##############################################
@app.get("/washhall")
def get_washhall():
    try:
        db, cursor = x.db()

        q = "SELECT * FROM car_wash_hall_info"
        cursor.execute(q)
        car_wash_hall_info = cursor.fetchall()

        if not car_wash_hall_info:
            return jsonify(error="No washhalls found"), 404

        return jsonify(car_wash_hall_info=car_wash_hall_info)

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


##############################################
@app.get("/favorites")
@jwt_required()
def get_favorites():
    try:
        user_fk = get_jwt_identity()

        db, cursor = x.db()

        q = """ 
            SELECT car_wash_locations.* 
            FROM car_wash_locations 
            JOIN favorites 
                ON car_wash_locations.location_pk = favorites.car_wash_location_fk 
            WHERE favorites.user_fk = %s;
        """

        cursor.execute(q, (user_fk,))
        favorites = cursor.fetchall()

        return jsonify(favorites=favorites), 200
    
    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500
    
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################################
@app.post("/favorites")
@jwt_required()
def add_favorite():
    try:
        data = request.get_json()

        user_fk = get_jwt_identity()
        car_wash_location_fk = data.get("location_pk")
        favorit_pk = uuid.uuid4().hex

        if not car_wash_location_fk:
            return jsonify(error="Missing location_pk"), 400

        db, cursor = x.db()

        q = "INSERT INTO favorites VALUES (%s, %s, %s)"
        cursor.execute(q, (favorit_pk, user_fk, car_wash_location_fk))
        db.commit()

        return jsonify(message="Favorite added"), 201

    except Exception as ex:
        ic(ex)

        if "1062" in str(ex):
            return jsonify(error="Favorite already exists"), 409

        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

##############################################
@app.delete("/favorites/<location_pk>")
@jwt_required()
def remove_favorit(location_pk):
    try:
        user_fk = get_jwt_identity()

        db, cursor = x.db()

        q = "DELETE FROM favorites WHERE user_fk = %s AND car_wash_location_fk = %s"
        cursor.execute(q, (user_fk, location_pk))
        db.commit()

        return jsonify(message="Favorite removed"), 200

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()  