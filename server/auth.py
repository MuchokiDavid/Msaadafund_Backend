from flask import  Blueprint, jsonify, request, make_response
from models import User, bcrypt, db,TokenBlocklist, Organisation
from flask_jwt_extended import create_access_token,create_refresh_token, get_jwt_identity,jwt_required,get_jwt
from utility import sendMail
import re
from google.oauth2 import id_token,credentials as google_credentials
# from google.oauth2.credentials import Credentials
from google.auth.transport import requests
# from googleapiclient.discovery import build
import os
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint("auth", __name__)

# import mail from app
CLIENT_ID = os.getenv("CLIENT_ID")

# signup for user 
@auth_bp.route("/user/register", methods=["POST"])
def register_user():
    from app import logging
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400

    # Extracting user data from request
    firstName = data.get('firstName')
    lastName = data.get('lastName')
    username = data.get('username')
    email = data.get('email')
    # nationalId = data.get('nationalId')
    phoneNumber = data.get('phoneNumber')
    # address = data.get('address')
    hashed_password = data.get('password')

    # Validating if required fields are present
    if not all([firstName, lastName, username, email, phoneNumber, hashed_password]):
        return jsonify({"error": "Missing required fields"}), 400

    # Checking for existing user data
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({"error": "Username already exists"}), 400

    existing_email = User.query.filter_by(email=email).first()
    if existing_email:
        return jsonify({"error": "Email already exists"}), 400


    existing_phone_number = User.query.filter_by(phoneNumber=phoneNumber).first()
    if existing_phone_number:
        return jsonify({"error": "Phone number already exists"}), 404
    try:
        # Creating new user instance
        new_user = User(firstName=firstName,
                        lastName=lastName,
                        username=username,
                        email=email,
                        # nationalId=nationalId,
                        phoneNumber=phoneNumber,
                        # address=address,
                        password=hashed_password)

        # Adding user to the database
        db.session.add(new_user)
        db.session.commit()
        sendMail.send_user_signup_mail(new_user)
        return jsonify({
            "message": "User registered successfully",
            "user":new_user.serialize()
        }), 200
    except  Exception as e:
        db.session.rollback()
        logging.error(e)
        print("Error in user register route: ", str(e))
        return jsonify({"error": "Failed to create account"}), 500

# login for user
@auth_bp.route('/user/login', methods=["POST"])
def login(): 
    data = request.get_json()
    username = data.get('username')

    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', username):
        # user login
        user = User.query.filter_by(email=username, isActive = True).first()
    else:
        user = User.query.filter_by(username=username, isActive = True).first()
    
    if not user:
        return jsonify({'error': 'User not registered'}), 401 
    
    if user.role in ('User', 'Admin'):
        if user.hashed_password == '' or user.hashed_password == None:
            return jsonify({'error': 'Invalid credentials'}), 401
        if not bcrypt.check_password_hash(user.hashed_password, data.get('password')):
            return jsonify({'error': 'Invalid credentials'}), 401 
        
        # check if user is a signatory
        is_signatory = bool(user.signatories)


        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)  
        
        return jsonify({
            "message": 'Welcome {}'.format(user.firstName),
            "tokens": {
                "access": access_token,
                "refresh": refresh_token
            },
            "user": user.serialize(),
            "is_signatory": is_signatory
        }), 200
    else: 
        return jsonify({'error':'Unauthorized user'}), 401

@auth_bp.route('/user/google-login', methods=["POST"])
def google_login():
    token = request.json.get('token')
    if not token:
        return jsonify({'error': 'Missing token'}), 400
    try:
        # Verify Google OAuth token
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            CLIENT_ID
        )

        # Ensure the token is issued by Google
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return jsonify({'error': 'Wrong issuer.'}), 400

        # Extract user information
        user_id = idinfo['sub']
        user_email = idinfo['email']

        # Check if user exists in your database
        user = User.query.filter_by(email=user_email, isActive=True).first()

        if not user:
            # If user does not exist, create a new account
            user = User(
                firstName=idinfo.get('given_name', 'Unknown'),
                lastName=idinfo.get('family_name', ''),
                username=idinfo.get('email', ''),
                email=user_email,
                hashed_password='',
                phoneNumber='',
                isActive=True,
                role='User'
            )
            db.session.add(user)
            db.session.commit()
        
        is_signatory = bool(user.signatories)

        # Generate access token for the user
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)  

        # Return response with JWT and user data
        return jsonify({
            "message": 'Welcome {}'.format(user.firstName),
            "access_token": access_token,
            "refresh": refresh_token,
            "user": user.serialize(),
            "is_signatory": is_signatory
        }), 200

    except ValueError as e:
        print(e)
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(e)
        return jsonify({'error': 'An error occurred'}), 500


# signup organisation
@auth_bp.route("/organisation/register", methods=["POST"])
def register_organisation():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    orgName = data.get('name')
    orgEmail = data.get('email')
    orgPassword = data.get('password')
    orgAddress = data.get('address')
    orgPhoneNumber = data.get('phoneNumber')

    if not orgName or not  orgEmail or not orgPassword or not orgAddress or not orgPhoneNumber:
         return jsonify({'error':'Missing fields'}),400

    existing_orgName = Organisation.query.filter_by(orgName=orgName).first()
    if existing_orgName:
        return {"error": "An organisation with this name already exists."},400
    
    existing_orgEmail =  Organisation.query.filter_by(orgEmail=orgEmail).first()
    if existing_orgEmail:
        return{"error":"This email is already registered to an organization"},400
    
    existing_orgPhoneNumber =  Organisation.query.filter_by(orgPhoneNumber=orgPhoneNumber).first()
    if existing_orgPhoneNumber:
        return{"error":"This Phone number is already registered to an organization"}, 400
    try:
        new_organisation =  Organisation(orgName=orgName.strip(), orgEmail=orgEmail, password=orgPassword,orgPhoneNumber=orgPhoneNumber, orgAddress=orgAddress)
        db.session.add(new_organisation)
        db.session.commit()

        if sendMail.send_registration_email(orgEmail, orgName):
            sendMail.send_org_notification_mail(orgName, orgEmail,orgPhoneNumber)
            return jsonify({"message": "Organization registered successfully and email sent",
                            "organisation":new_organisation.serialize()
                            }), 200
        else:
            return jsonify({"message": "Organization registered successfully but failed to send email"}), 500
    except  Exception as e:
        print(e)
        db.session.rollback()
        return jsonify({"error": "Registration Failed"}), 500


@auth_bp.route('/organisation/login',methods=['POST'])
def login_Organisation(): 
    data = request.get_json()
    orgEmail = data.get('email')
    password = data.get('password')
    try:
        organisation  = Organisation.query.filter_by(orgEmail=orgEmail).first()
        if not organisation :
            return jsonify({"error":"Organisation does not exist"}),401

        if not organisation.check_password(password):
            return jsonify({"error":"Invalid Password"}),401
        
        if organisation.isVerified==False:
            sendMail.send_org_verification_mail(organisation)
            return {"error":"Account is not verified. Please contact us for verification"},403
        
        access_token = create_access_token(identity=organisation.id)
        refresh_token = create_refresh_token(identity=organisation.id)

        return jsonify({
                'message': 'Welcome {}'.format(organisation.orgName),
                'tokens':{
                    'access_token': access_token,
                    'refresh_token': refresh_token
                },
                "organisation": organisation.serialize()}),200
    except Exception as e:
        print(e)
        return {'error':str(e)},500



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

# Get a new token with a refresh token
@auth_bp.route('/refresh', methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    access_token = create_access_token(identity=identity, fresh=False)
    return jsonify(access_token=access_token)
    