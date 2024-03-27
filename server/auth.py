from flask import Blueprint, jsonify, request, make_response
from models import User, bcrypt, db,TokenBlocklist
from flask_jwt_extended import create_access_token,create_refresh_token,jwt_required,get_jwt

auth_bp = Blueprint("auth", __name__)

# signup for user 
@auth_bp.post("/register") 
def register_user():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    # Extracting user data from request
    firstName = data.get('firstName')
    lastName = data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    nationalId = data.get('nationalId')
    phoneNumber = data.get('phoneNumber')
    address = data.get('address')
    hashed_password = data.get('password')

    # Validating if required fields are present
    if not all([firstName, lastName, username, email, nationalId, phoneNumber, address, hashed_password]):
        return jsonify({"error": "Missing required fields"}), 400

    # Checking for existing user data
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400

    existing_national_id = User.query.filter_by(nationalId=nationalId).first()
    if existing_national_id:
        return jsonify({"error": "National ID already exists"}), 400

    existing_phone_number = User.query.filter_by(phoneNumber=phoneNumber).first()
    if existing_phone_number:
        return jsonify({"error": "Phone number already exists"}), 400

    # Creating new user instance
    new_user = User(firstName=firstName,
                    lastName=lastName,
                    username=username,
                    email=email,
                    nationalId=nationalId,
                    phoneNumber=phoneNumber,
                    address=address,
                    password=hashed_password)

    # Adding user to the database
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "message": "User registered successfully",
    }), 200

# login for user

@auth_bp.post('/login')
def login(): 
    data = request.get_json()
    username = data['username']
    user = User.query.filter_by(username = username).first()
    if not user:
        return {'error': 'User not registered'}, 401 
    
    if not bcrypt.check_password_hash(user.hashed_password,data['password']):
                return {'error': '401 Unauthorized'}, 401 

    access_token = create_access_token(identity=user.username)
    refresh_token = create_refresh_token(identity=user.username)  
    return jsonify(
        {
            "message": "logged in",
            "tokens": {
                "access": access_token,
                "refresh": refresh_token
            }
        }

    ), 200

# logout for user
@auth_bp.get('/logout')
@jwt_required(verify_type=False) #false provides both access and refresh tokens
def logout_user():
    jwt = get_jwt()

    jti = jwt['jti']
    token_type = jwt['type']

    token_blocklist = TokenBlocklist(jti=jti)

    db.session.add(token_blocklist)
    db.session.commit()

    return jsonify({"message":f"{token_type} token revoked successfully"}),200
    