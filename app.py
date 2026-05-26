from flask import Flask, request, jsonify, redirect
import uuid
import time # EPOCH, timestamp
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

import x

from flask_cors import CORS

from datetime import timedelta # For JWT token expiration

from icecream import ic
ic.configureOutput(prefix=f"___ | ", includeContext=True)

from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity # From chatGPT (jwt)

app = Flask(__name__)
CORS(app)  # allows everything

app.config["JWT_SECRET_KEY"] = "super-secret-key" # From chatGPT (jwt)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=7)
jwt = JWTManager(app)


#######################################################################################
#                                     SIGN UP                                        #
#######################################################################################

                    # POST SIGN UP #
############################################################
@app.post("/sign-up")
def sign_up():
    try:
        ic(request.json)

        # TODO: Validate user data
        verification_key = uuid.uuid4().hex
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()
        user_created_at = int(time.time())
        user_verified_at = 0
        user_forgot_password = 0
        password = x.validate_user_hashed_password()
        has_sub = 0
        sub_type = None
        
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
        q = "INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(q, (user_pk, user_first_name, user_last_name, user_email, user_hashed_password, user_created_at, user_verified_at, user_verification_key, user_reset_password_key, has_sub, sub_type, user_deleted_at))

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

        x.send_email("Velkommen til Washworld! - Aktiver din konto", html)
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
        
        # Dublikeret email eller nummerplade
        if "1062" in str(ex) and "user_email" in str(ex):
            return jsonify(error_code="email_taken"), 409
        if "1062" in str(ex) and "plate_number" in str(ex):
            return jsonify(error_code="plate_taken"), 409

        # Worst case
        return f"""<browser>System under maintenance</browser>""", 500
        
    finally: 
        if "cursor" in locals(): cursor.close() # Locals refers to anything inside the try or except
        if "db" in locals(): db.close() # db refers to anything inside the database


                # POST CHECK EMAIL #
############################################################
@app.post("/check-email")
def check_email():
    try:
        user_email = x.validate_user_email()

        db, cursor = x.db()
        cursor.execute("SELECT user_email FROM users WHERE user_email = %s", (user_email,))
        user = cursor.fetchone()

        if user:
            return jsonify(error_code="email_taken"), 409

        return jsonify(message="Email available"), 200

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


                # PATCH RESEND VERIFICATION #
############################################################
@app.patch("/resend-verification")
def resend_verification():
    try:
        user_email = x.validate_user_email()

        db, cursor = x.db()

        cursor.execute("SELECT * FROM users WHERE user_email = %s AND user_verified_at = 0", (user_email,))
        user = cursor.fetchone()

        if not user:
            return jsonify(error_code="user_not_found"), 404

        # Generer ny verification key
        new_verification_key = uuid.uuid4().hex

        cursor.execute(
            "UPDATE users SET user_verification_key = %s WHERE user_email = %s",
            (new_verification_key, user_email)
        )
        db.commit()

        html = f"""
            <h1>Velkommen til Washworld!</h1>
            <p>Klik på linket herunder for at aktivere din konto:</p>
            <a href="http://localhost:3000/verify/{new_verification_key}">Aktiver konto</a>
        """
        x.send_email("Aktiver din konto", html)

        return jsonify(message="Verification email resent"), 200

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


                # GET VERIFY ACCOUNT #
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


#######################################################################################
#                                     LOG IN                                         #
#######################################################################################

                    # POST LOGIN #
############################################################
@app.post("/")
def login():
    try:
        # TODO: Validate user data
        user_email = x.validate_user_email()
        password = x.validate_user_hashed_password()

        # TODO: Connect to the database og finder brugeren i databasen
        db, cursor = x.db()
        q = "SELECT * FROM users WHERE user_email = %s"
        cursor.execute(q, (user_email,))
        user = cursor.fetchone()

        # Tjek at brugeren findes og at password matcher
        if not user or not check_password_hash(user["user_hashed_password"], password): # sammenligner det indtastede password med det hashede i databasen
            return jsonify(error="Invalid email or password"), 401

        # Create JWT token
        access_token = create_access_token(identity=user["user_pk"]) # user_pk gemmes INDE I tokenet
        return jsonify(access_token=access_token, user_first_name=user["user_first_name"], user_email=user["user_email"]), 200
        
    
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


#######################################################################################
#                                   FORGOT PASSWORD                                  #
#######################################################################################

                # POST FORGOT PASSWORD #
############################################################
@app.post("/forgot-password")
def forgot_password():
    try:
        user_email = x.validate_user_email()

        db, cursor = x.db()

        # Tjek om emailen findes
        cursor.execute("SELECT * FROM users WHERE user_email = %s", (user_email,))
        user = cursor.fetchone()

        if not user:
            return jsonify(error_code="email_not_found"), 404

        # Generer ny reset-nøgle
        reset_key = uuid.uuid4().hex

        # Gem nøglen i databasen
        cursor.execute(
            "UPDATE users SET user_reset_password_key = %s WHERE user_email = %s",
            (reset_key, user_email)
        )
        db.commit()

        # Send email med reset-link
        html = f"""
            <h1>Nulstil din adgangskode</h1>
            <p>Klik på linket herunder for at nulstille din adgangskode:</p>
            <a href="http://localhost:3000/reset-password/{reset_key}">Nulstil adgangskode</a>
        """
        x.send_email("Nulstil adgangskode", html)

        return jsonify(message="Email sent"), 200

    except Exception as ex:
        ic(ex)
        if "company_exception email" in str(ex):
            return jsonify(error_code="email_not_found"), 400

        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()
    

#######################################################################################
#                                     RESET PASSWORD                                  #
#######################################################################################

                # GET RESET PASSWORD #
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


                # POST RESET PASSWORD #
############################################################
@app.post("/reset-password/<key>")
def reset_password(key):
    try:
        # TODO: Validate key
        validated_key = x.validate_uuid4(key)

        # TODO: Validate new password
        password = x.validate_user_hashed_password()
        confirm_password = request.json.get("confirm_password", "").strip()

        # If passwords not match, make a error
        if password != confirm_password:
            return jsonify(error_code="passwords_do_not_match"), 400

        # Hash password
        new_hashed_password = generate_password_hash(password)

        # TODO: Connect to the database
        db, cursor = x.db()

        # Update new password where key matches
        q = """
            UPDATE users 
            SET user_hashed_password = %s 
            WHERE user_reset_password_key = %s
        """
        cursor.execute(q, (new_hashed_password, validated_key))
        db.commit()

        # Hvis ingen rækker blev opdateret, var nøglen ikke gyldig
        if cursor.rowcount == 0:
            return jsonify(error_code="invalid_key"), 404

        return jsonify(message="Password changed, please login"), 200

    except Exception as ex:
        ic(ex)

        if "company_exception user_hashed_password" in str(ex):
            return jsonify(error_code="invalid_password"), 400

        if "company_exception uuid4 invalid" in str(ex):
            return jsonify(error_code="invalid_key"), 400

        # Worst case
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


#######################################################################################
#                                   SUBSCRIPTIONS                                    #
#######################################################################################


                    # POST SUBSCRIPTION #
############################################################
@app.post("/subscription")
@jwt_required()
def add_subscription():
    try:
        db, cursor = x.db()

        data = request.get_json()

        has_sub = 1
        sub_type = (data.get("sub_type") or "").strip()

        q = "UPDATE users SET has_sub = %s, sub_type = %s WHERE user_pk = %s"
        cursor.execute(q, (has_sub, sub_type, get_jwt_identity()))
        db.commit()

        return {"message": "Subscription added"}, 200

    except Exception as ex:
        ic(ex)
        return {"error": "System under maintenance"}, 500

    finally:
        if "cursor" in locals():
            cursor.close()
        if "db" in locals():
            db.close()

         # GET SUBSCIPTION STATUS AND TYPE #
############################################################
@app.get("/subscription/status")
@jwt_required()
def get_subscription_status():
    try:
        db, cursor = x.db()

        q = "SELECT has_sub, sub_type FROM users WHERE user_pk = %s"
        cursor.execute(q, (get_jwt_identity(),))
        row = cursor.fetchone()

        if not row:
            return {"error": "User not found"}, 404

        # Returnerer true eller false baseret på has_sub værdien i databasen (1 for true, 0 for false)
        return {"has_sub": bool(row["has_sub"]), "sub_type": row["sub_type"]}, 200

    except Exception as ex:
        ic(ex)
        return {"error": "System under maintenance"}, 500
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()

#######################################################################################
#                              PROFILE INFORMATION                                   #
#######################################################################################
 
            # GET PROFILE INFORMATION #
############################################################
@app.get("/profile-information")
@jwt_required()
def get_profile_information():
    try:
        user_pk = get_jwt_identity()
 
        db, cursor = x.db()
 
        q = """
            SELECT 
                users.user_first_name,
                users.user_last_name,
                users.user_email,
                license_plate.plate_number
            FROM users
            LEFT JOIN license_plate ON license_plate.user_fk = users.user_pk
            WHERE users.user_pk = %s
        """
 
        cursor.execute(q, (user_pk,))
        user = cursor.fetchone()
 
        if not user:
            return jsonify(error="User not found"), 404
 
        return jsonify(user=user), 200
 
    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500
 
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()
 
 
            # PATCH PROFILE INFORMATION #
############################################################
@app.patch("/profile-information")
@jwt_required()
def update_profile_information():
    try:
        user_pk = get_jwt_identity()
 
        user_first_name = x.validate_user_first_name()
        user_last_name = x.validate_user_last_name()
        user_email = x.validate_user_email()
 
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
 
        if cursor.rowcount == 0:
            return jsonify(error="User not found"), 404
 
        return jsonify(message="Profile updated"), 200
 
    except Exception as ex:
        ic(ex)
        if "1062" in str(ex) and "user_email" in str(ex):
            return jsonify(error_code="email_taken"), 409
        return jsonify(error="System under maintenance"), 500
 
    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


#######################################################################################
#                                     DELETE USER                                    #
#######################################################################################

                        # DELETE USER #
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


#######################################################################################
#                                       LOCATIONS                                    #
#######################################################################################

                    # GET LOCATIONS #
############################################################
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



        # GET SINGLE LOCATION #
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


        # GET WASH HALLS FOR LOCATION #
############################################## skal måske slettes ?
@app.get("/wash-hall/<location_pk>")
def get_wash_halls(location_pk):
    try:
        db, cursor = x.db()

        q = """
        SELECT car_wash_hall_info.car_wash_hall_number
        FROM car_wash_hall_info
        INNER JOIN car_wash_locations
        ON car_wash_hall_info.car_wash_location_fk = car_wash_locations.location_pk
        WHERE car_wash_locations.location_pk = %s;
        """

        cursor.execute(q, (location_pk,))
        wash_halls = cursor.fetchall()

        if not wash_halls:
            return jsonify(error="No washhalls found for this location"), 404

        return jsonify(wash_halls=wash_halls)

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500

    finally:
        if "cursor" in locals(): cursor.close()
        if "db" in locals(): db.close()


#######################################################################################
#                           CAR WASH HISTORY                                      #
#######################################################################################

        # GET CAR WASH HISTORY #
##############################################
@app.get("/car-wash-history/user/<user_pk>")
def get_car_wash_history(user_pk):
    try:
        db, cursor = x.db()

        # Henter alle vaske for en bruger ved at gå gennem nummerpladen
        q = """
        SELECT 
            car_wash_history.car_wash_history_pk,
            car_wash_locations.location_name,
            car_wash_history.date_of_wash,
            car_wash_history.car_wash_type,
            car_wash_history.car_wash_price
        FROM car_wash_history
        JOIN car_wash_locations ON car_wash_history.car_wash_location_fk = car_wash_locations.location_pk
        JOIN license_plate ON car_wash_history.license_plate_fk = license_plate.license_plate_pk
        JOIN users ON license_plate.user_fk = users.user_pk
        WHERE users.user_pk = %s
        """

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


            # POST CAR WASH HISTORY (RECIEPT) #
############################################################
@app.post("/reciept")
@jwt_required()
def add_car_wash_history():
    try:
        data = request.get_json()

        car_wash_history_pk = uuid.uuid4().hex

        user_fk = get_jwt_identity()

        db, cursor = x.db()

        # Hent brugerens nummerplade
        cursor.execute("""
            SELECT license_plate_pk
            FROM license_plate
            WHERE user_fk = %s
        """, (user_fk,))

        plate = cursor.fetchone()

        if not plate:
            return jsonify(error="License plate not found"), 404

        license_plate_fk = plate["license_plate_pk"]

        car_wash_location_fk = data.get("car_wash_location_fk")
        car_wash_hall_fk = data.get("car_wash_hall_fk")

        date_of_wash = int(time.time())

        car_wash_price = data.get("car_wash_price")
        car_wash_type = data.get("car_wash_type")
        car_wash_started_at = data.get("car_wash_started_at")
        car_wash_ended_at = data.get("car_wash_ended_at")

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

#######################################################################################
#                                    FAVORITES                                        #
#######################################################################################

            # GET FAVORITES #
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


              # POST FAVORITE #
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

#det er mere sikkert at bruge parameterized queries (med %s) for at undgå SQL injection, selvom user_fk 
# kommer fra JWT og burde være sikkert, er det en god praksis at altid bruge parameterized queries
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


            # DELETE FAVORITE #
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


#######################################################################################
#                                    FEEDBACK                                        #
#######################################################################################

                    # POST FEEDBACK #
############################################################
@app.post("/feedback")
@jwt_required()  
def feedback():
    try:
        data = request.get_json()
        rating = data.get("rating")
        comment = data.get("comment")
        feedback_pk = uuid.uuid4().hex
        created_at = int(time.time())
    
        # Skal disse måske valideres med x-fil?
        user_fk = get_jwt_identity()
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


#######################################################################################
#                                    DAMAGE REPORT                                    #
#######################################################################################

            # POST DAMAGE REPORT #
##############################################
@app.post("/damage-report")
@jwt_required()
def send_damage_report():
    try:
        data = request.json
        description = (data.get("description") or "").strip()
        user_email = (data.get("user_email") or "Ukendt").strip() # Brugerens email hentes fra request-body og inkluderes i emailens indhold, så Washworld ved hvem der har indsendt rapporten

        # Validate that description is not empty
        if not description:
            return jsonify(error="Description mangler"), 400

        # Build the email HTML body
        html = f"""
            <h1>Skaderapport</h1>
            <p><strong>Fra:</strong>{user_email}</p>
            <p><strong>Beskrivelse:</strong>{description}</p>
        """
        x.send_damage_report_email("Skaderapport", html, user_email)
        return jsonify(message="Skaderapport sendt"), 200

    except Exception as ex:
        ic(ex)
        return jsonify(error="System under maintenance"), 500
    