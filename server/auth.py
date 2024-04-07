from flask import  Blueprint, jsonify, request, make_response
from models import User, bcrypt, db,TokenBlocklist, Organisation
from flask_jwt_extended import create_access_token,create_refresh_token, get_jwt_identity,jwt_required,get_jwt
from utility import sendMail


auth_bp = Blueprint("auth", __name__)

# import mail from app

# signup for user 
@auth_bp.route("/user/register", methods=["POST"])
def register_user():
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

    # existing_national_id = User.query.filter_by(nationalId=nationalId).first()
    # if existing_national_id:
    #     return jsonify({"error": "National ID already exists"}), 400

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
        print("Error in user register route: ", str(e))
        return jsonify({"error": "Failed to create account"}), 500

# login for user
@auth_bp.route('/user/login', methods=["POST"])
def login(): 
    data = request.get_json()
    username = data.get('username')
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({'error': 'User not registered'}), 401 
    
    if user.role in ('User', 'Admin'):
        if not bcrypt.check_password_hash(user.hashed_password, data.get('password')):
            return jsonify({'error': 'Invalid credentials'}), 401 

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)  
        
        return jsonify({
            "message": 'Welcome {}'.format(user.firstName),
            "tokens": {
                "access": access_token,
                "refresh": refresh_token
            },
            "user": user.serialize()
        }), 200
    else: 
        return jsonify({'error':'Unauthorized user'}), 401

# signup organisation
@auth_bp.route("/organisation/register", methods=["POST"])
def register_organisation():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid request data"}), 400
    
    orgName = data['name']
    orgEmail = data['email']
    orgPassword = data['password']
    orgAddress = data['address']
    orgPhoneNumber = data['phoneNumber']

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
        new_organisation =  Organisation(orgName=orgName, orgEmail=orgEmail, password=orgPassword,orgPhoneNumber=orgPhoneNumber, orgAddress=orgAddress)
        db.session.add(new_organisation)
        db.session.commit()

        if sendMail.send_registration_email(orgEmail, orgName):
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
            return {"error":"Account is not verified. Please check your email for verification"},403
        
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
    