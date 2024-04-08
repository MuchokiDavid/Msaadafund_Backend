#Flask app
from flask import Flask, request,jsonify,make_response
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation,Account,TokenBlocklist, Enquiry
from utility import check_wallet_balance, sendMail, OTPGenerator
import os
from dotenv import load_dotenv
load_dotenv()
from intasend import APIService
import uuid
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt
import requests
from datetime import datetime
from flask_jwt_extended import JWTManager,jwt_required,get_jwt_identity
from flask_mail import Mail, Message
from auth import auth_bp
# from views import view_bp
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from views import UserAdminView,DonationAdminView,CampaignAdminView,OrganisationAdminView,AccountAdminView
from cloudinary.uploader import upload
import cloudinary.api

#fetch environment variables  for the api key and server url
token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
service = APIService(token=token,publishable_key=publishable_key, test=True)

app = Flask(__name__)
admin = Admin(app, name='My Admin Panel', template_mode='bootstrap4')

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 60 * 60
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['OTP_STORAGE'] = {}


migrate = Migrate(app, db)
db.init_app(app)
# admin.init_app(app)
api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager()
jwt.init_app(app)
mail = Mail(app)


cloudinary.config( 
  cloud_name = "dml7sp2zm", 
  api_key = "111134481418281", 
  api_secret = "Mr7c7aIxfPPx4p0xDLcqGjuoEl8" 
)

# register blueprint
app.register_blueprint(auth_bp, url_prefix='/api/v1.0/auth')
# register views
# app.register_blueprint(view_bp, url_prefix ='/auths')

# Register the models with Flask-Admin
admin.add_view(UserAdminView(User, db.session))
admin.add_view(CampaignAdminView(Campaign, db.session))
admin.add_view(DonationAdminView(Donation, db.session))
admin.add_view(OrganisationAdminView(Organisation, db.session))
admin.add_view(AccountAdminView(Account, db.session))
admin.add_view(ModelView(TokenBlocklist, db.session))

# jwt error handler
@jwt.expired_token_loader
def expired_token(jwt_header,jwt_data):
    return jsonify({'error': 'The token has expired.','error':'token expired'}), 401

@jwt.invalid_token_loader
def invalid_token(error):
    return jsonify({'error': 'Does not contain a valid token.','error':'invalid token'}), 401

@jwt.unauthorized_loader
def missing_token(error):
    return jsonify({'error': 'Request does not contain an access token.', 'error':'token missing'}), 401


@jwt.token_in_blocklist_loader #check if the jwt is revocked
def token_in_blocklist(jwt_header,jwt_data):
    jti = jwt_data['jti']

    token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()
# if token is none : it will return false 
    return token is not None

@app.route("/")
def index():
    """Home page."""""
    return "<h3>Msaada Mashinani</h3>"

# classes for users
class userData (Resource):
    def get(self):
        users = [user.serialize() for user in User.query.filter_by(isActive = True).all()]
        response = make_response(jsonify(users), 200)
        return response
  

class userDataByid(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"error":"User not found"}, 404
        response = make_response(jsonify(user.serialize()),200)
        return response
    
    @jwt_required()     
    def patch(self):
        current_user = get_jwt_identity()
        data = request.get_json()
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        phoneNumber = data.get('phoneNumber')
        address = data.get('address')

        existing_user = User.query.filter_by(username = current_user).first()
        if not existing_user:
            return{ "error":"User not found"}, 404

        if firstName:
            existing_user.firstName = firstName
        if lastName:
            existing_user.lastName = lastName
        if phoneNumber:
            existing_user.phoneNumber = phoneNumber
        if address:
            existing_user.address = address
        if 'isActive' in data:
            existing_user.isActive = data['isActive']

        db.session.commit()

        response = make_response(jsonify(existing_user.serialize()),200)
        return response
  
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username = current_user).first()
        if not user:
            return jsonify({'error':"User not found"}), 404
        else:
            user.isActive = False       
            # db.session.delete(user)
            db.session.commit()

            return {"message": "User deactivated successfully"},200   
        
@app.route("/api/v1.0/setCampaign", methods=["POST"])
@jwt_required()
def post():
    current_user = get_jwt_identity()
    campaignName = request.form.get('campaignName')
    description = request.form.get('description')
    category = request.form.get('category')
    startDateStr = request.form.get('startDate')
    endDateStr = request.form.get('endDate')
    targetAmount = request.form.get('targetAmount')
    banner = request.files.get('banner') 
    
    
    available_org= Organisation.query.filter_by(id=current_user).first()
    if not available_org:
        return jsonify({"error":"Organisation does not exist."}),404
    print(available_org.orgName)

    # Convert date strings to Python date objects
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()

    print(startDate, endDate)
    current_date = datetime.now().date()
    if startDate < current_date:
        return {'error': 'cannot create a campaign in the past'}, 400 
    if endDate < current_date:
        return {'error':'enddate  should be greater than current date'} ,400  
    if endDate < startDate:
        return {'error': 'end date cannot be before start date'}, 400
 
    if not (campaignName and description and startDate and endDate):
        return jsonify({"error":"Please provide complete information"}),400
    print(description)
    
    if startDate == current_date:
        isActive = True
    elif startDate > current_date:
        isActive = False
    elif endDate > current_date:
        isActive = False

    try:
        # Upload the banner image to Cloudinary
        result = upload(banner)
        if "secure_url" in result:
            new_campaign = Campaign(
                campaignName=campaignName,
                description=description,
                category=category,
                banner=result["secure_url"],
                startDate=startDate,
                endDate=endDate,
                targetAmount=float(targetAmount),
                isActive=isActive,
                org_id=available_org.id
            )

            #create wallet
            try:
                response = service.wallets.create(currency="KES",  label=str(uuid.uuid4()), can_disburse=True)

                if response.get('type') == 'client_error':
                    return jsonify({"error":response.get('errors')[0].get('detail')}),400

                new_campaign.walletId=response.get("wallet_id")
            except Exception as e:
                return {"error": str(e)}, 404
            
            try:
                db.session.add(new_campaign)
                db.session.commit()
                sendMail.send_post_campaign(available_org, campaignName, description, category, targetAmount, startDate,endDate)


            except Exception as e:
                print(e)
                return jsonify({"Error": "Something went wrong while creating your campaign"}),500
            return jsonify(new_campaign.serialize()),200

        else:
            return {"error": "Failed to upload banner to Cloudinary"},404
    except Exception as e:
        return {"error": str(e)}, 404
    

#get campaigns
class campaignData(Resource):
    # @jwt_required()
    def get(self):
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=10, type=int)
        campaigns = Campaign.query.filter_by(isActive=True).paginate(page=page, per_page=per_page)
        data = [campaign.serialize() for campaign in campaigns.items]
        response = make_response(jsonify(data), 200)
        return response
       
   

#Get inactive campaigns
@app.route('/api/v1.0/get_inactive', methods=['GET'])
def  getInactiveCampaign():
    """Return a list of all inactive campaigns"""
    all_campaigns = [campaign.to_dict() for campaign in Campaign.query.filter_by(isActive=False).all()]
    response = make_response(jsonify(all_campaigns), 200)
    return response

#Get one campaign by id in unprotected route
@app.route("/campaign/<int:campaignId>", methods=["GET"])
def readOne(campaignId):
    """Get the details of one specific campaign."""
    try:
        campaign = Campaign.query.get(campaignId)
    except Exception as e:
        print(e)
        return jsonify({"error":f"Invalid campaign ID: {campaignId}"}), 400

    # Return the serialized campaign
    return jsonify(campaign.serialize())

#Get  specific campaign details by id
class campaignById(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        campaign = Campaign.query.filter_by(org_id=current_user).all()
        if not campaign:
            return {"error":"Campaign not found"}, 404
        data = [camp.serialize() for camp in campaign]
        response = make_response(jsonify(data), 200)
        return response
    
    @jwt_required()
    def patch (self):
        data=request.get_json()
        description = data.get('description')
        endDate = data.get('endDate')
        targetAmount = data.get('targetAmount')

        current_user = get_jwt_identity()
        existing_campaign = Campaign.query.filter_by(org_id=current_user).first()
        if not existing_campaign:
            return {"error":"Campaign not found"}, 404
        if description:
            existing_campaign.description = description
        if endDate:
            existing_campaign.endDate =endDate
        if targetAmount:
            existing_campaign.targetAmount = float(targetAmount)

        db.session.commit()

        response = make_response(jsonify(existing_campaign.serialize()), 200)
        return response

    @jwt_required()
    def delete(self):
        data=request.get_json()
        current_user = get_jwt_identity()
        organisation = Organisation.query.filter_by(id=current_user).first()
        
        if not organisation:
            return jsonify({'error':"Organisation not found"}), 404
        
        existing_campaign = Campaign.query.filter_by(campaignName=data['name']).first()
        if not existing_campaign:
            return jsonify({'error':"Campaign not found"}), 404
        else:
            existing_campaign.isActive = False       
            # db.session.delete(campaign)
            db.session.commit()

            return {"message": "Campaign deactivated successfully"},200   


#Get wallet balance for a campaign
@app.route('/api/v1.0/campaign_wallet/<int:id>', methods=['GET'])
@jwt_required()
def check_wallet(id):
    current_user_id = get_jwt_identity()
    existing_org = Organisation.query.filter_by(id=current_user_id).first()
    if not existing_org:
        return jsonify({"error":"Organisation not found"}), 404
    
    existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
    if not existing_campaign:
        return jsonify({ "error":"Campaign not found"}), 404
    wallet_id= existing_campaign.walletId
    print(wallet_id)
    try:
        response = service.wallets.details(wallet_id)
        data = response
        if data.get("errors"):
            error_message = data.get("errors")
            return  make_response({ "error":error_message} , 400)

        return {'wallet_details': response}, 200
    except Exception as e:
        return { "error":"Internal server error"}
    
class addAccount(Resource):
    def get(self):
        all_accounts= Account.query.all()
        response_dict= [account.serialize() for account in all_accounts]
        response= make_response(jsonify(response_dict), 200)
        return response

#Get account by id
class accountById(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error":"Organisation not found"}, 404
        
        account = Account.query.filter_by(orgId=existing_organisation.id).all()
        if not account:
            return {"error":"Account not found"}, 404
        data = [acc.serialize() for acc in account]
        response = make_response(jsonify(data),200)
        return response
    
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error":"Organisation not found"}, 404
        
        data= request.get_json()
        accountType= data.get('accountType')
        accountNumber= data.get('accountNumber')
        try:
            new_account= Account(accountType=accountType, accountNumber=accountNumber, orgId=existing_organisation.id )
            db.session.add(new_account)
            db.session.commit()
            response = make_response(jsonify(new_account.serialize()),201)
            return response
        except Exception  as e:
             return {"error": "Account already registered"},400  

    
    @jwt_required()
    def delete(self):
        data = request.get_json()
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error":"Organisation not found"}, 404
        
    
        account = Account.query.filter_by(accountNumber=data['accountNumber']).first()
        if not account:
            return {"error":"Account not found"}, 404
        else:     
            db.session.delete(account)
            db.session.commit()

            return {"message": "Account deleted successfully"},200   

class Organization(Resource):
    def get(self):
        organizations = Organisation.query.all()
        serialized_organizations = [org.serialize() for org in organizations]
        return (serialized_organizations), 200

class OrganisationDetail(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id=current_user).first()
        if not org :
            return {'error':'Organisation does not exist'}, 404
        return make_response(jsonify(org.serialize()))
   
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id = current_user)
        if not org:
            return{'error': 'Organisation does not exist'} ,  404
        db.session.delete(org)
        db.session.commit()
        return {'message' : 'Organisation deleted successfully'}, 200
    
    @jwt_required()
    def patch(self):
        current_user = get_jwt_identity()
        data = request.get_json()
        orgName = data.get('orgName')
        # orgEmail = data.get('orgEmail')
        orgPhoneNumber = data.get('orgPhoneNumber')
        orgAddress = data.get('orgAddress')
        orgDescription = data.get('orgDescription')

        existing_org = Organisation.query.filter_by(id=current_user).first()
        if not existing_org:
            return {"error": "Organisation does not exist"}, 404
        
        if orgName:
            existing_org.orgName = orgName
        # if orgEmail:
        #     existing_org.orgEmail = orgEmail  #issue 2
        if orgPhoneNumber:
            existing_org.orgPhoneNumber = orgPhoneNumber
        if orgAddress:
            existing_org.orgAddress = orgAddress
        if orgDescription:
            existing_org.orgDescription = orgDescription

        db.session.commit()
        return {"message": "Organisation has been updated", "Data": existing_org.serialize()}

#Route to get banks and their code in intersend API
@app.route('/api/v1.0/all_banks', methods=['GET'])
def bank_data():
    url = "https://payment.intasend.com/api/v1/send-money/bank-codes/ke/"
    try:
        response = requests.get(url)
        data = response.json()
        return jsonify(data), 200
        
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while processing your request"}),500

# Route to withdraw money to M-pesa number
@app.route("/api/v1.0/withdraw",methods=["POST"])
@jwt_required()
def campaign_money_withdrawal():
    current_user = get_jwt_identity()
    organisation = Organisation.query.filter_by(id=current_user).first()
    if not organisation:
         return {"error":"organisation cannot be found"},404
    
    data=request.get_json()
    accountType= data.get("accountType")# M-Pesa or Bank
    accountName= data.get("accountName")# KCB, M-Pesa, Equity,Family bank, etc
    accountNumber= data.get("accountNumber")#bank account number and mpesa phone number
    amount=float(data.get('amount'))
    # orgId= int(data.get('orgId'))# use jwt_identity
    campaign=int(data.get("campaign"))
    # all_banks= bank_data()
    # print(all_banks)
    
    account= Account.query.filter_by(accountType=accountType,accountName=accountName,accountNumber=accountNumber,orgId=organisation.id).first()
    if account is None:
        return jsonify({"error": "No such account"}),404

    campaigns= Campaign.query.filter_by(id=campaign, org_id=organisation.id, isActive=True).first()
    if not campaigns:
        return jsonify({"error":"Campaign does not exist or inactive."}),404
    
    #check wallet balance
    if float(check_wallet_balance(campaigns.walletId))<float(amount):
        return jsonify({"error":"Insufficient funds in the wallet!"}),400
    try: 
        if accountType=="M-Pesa":
            #Initiate intasend M-Pesa transaction
            transactions = [{'name': organisation.orgName, 'account': account.accountNumber, 'amount': int(amount)}]

            response = service.transfer.mpesa(wallet_id=campaigns.walletId, currency='KES', transactions=transactions)
            if response.get('errors'):
                error_message= response.get('errors')[0].get('detail')
                return jsonify({'error':error_message})
            return jsonify(response)
        
        elif accountType=="Bank":
            return jsonify({"message":"Bank transaction will be here"})
        else:
            return jsonify({"error":"Select transaction"}),400

        
    except Exception as e :
        print(e)
        return jsonify({"error":str(e)}),500

#Intasend web hook for getting changes in transaction  status on mpesa stk push
@app.route('/api/v1.0/intasend-webhook', methods = ['POST'])
def webhook():
    try:
        payload = request.json
        # print(payload)
        
        invoice_id = payload.get('invoice_id')
        state = payload.get('state')
        donating_user=''

        donation = Donation.query.filter_by(invoice_id=invoice_id).first()
        if not donation:
            return  jsonify({"status":"Donation record not found"}),404
        if donation.user_id:
            donating_user= User.query.get(donation.user_id)

        donation_campaign= Campaign.query.get(donation.campaign_id)
        if not donation_campaign:
            return jsonify({'error':'campaign not listed'})
        
        campaign_organisation= Organisation.query.get(donation_campaign.org_id)
        if not campaign_organisation:
            return jsonify({'error':'Organisation not found'})
        
        if state == "COMPLETE":
            donation.status = "COMPLETE"
            db.session.commit()
            if donating_user:
                sendMail.send_mail_on_donation_completion(donation.amount, 
                                                        donation.donationDate, 
                                                        donating_user.Firstname, 
                                                        donation_campaign.campaignName,
                                                        donating_user.email, 
                                                        campaign_organisation.orgName)
        elif state == "PROCESSING":
            donation.status = "PROCESSING"
            db.session.commit()
        elif state== "FAILED":
            donation.status="FAILED"
            db.session.delete(donation)
            db.session.commit()
            if  donating_user:
                sendMail.send_mail_donation_not_successiful(donation.amount, 
                                                        donation.donationDate, 
                                                        donating_user.firstname, 
                                                        donation_campaign.campaignName, 
                                                        donating_user.email,
                                                        campaign_organisation.orgName)
        
        return jsonify({'message': 'Webhook received successfully'})
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid third party response'}), 400
    
#Express donations route for user who is not logged in
class  ExpressDonations(Resource):
    def post(self):
        data= request.get_json()
        email= "msaadaanonymous@gmail.com"
        phoneNumber= data.get("phoneNumber")
        amount= data.get('amount')
        campaign_id= data.get('campaignId')

        if not email:
            return make_response(jsonify({"error":"Email is required."}),400)
        
        if not phoneNumber:
            return make_response(jsonify({"error":"Phone number is required."}),400)

        if not amount:
            return make_response(jsonify({"error":"Amount is required."}),400)
        if int(amount) <5:
                return make_response(jsonify({"error":"Donation must be above Kshs 5."}),400)

        
        existing_campaign= Campaign.query.filter_by(id=campaign_id).first()
        if not existing_campaign:
            return  make_response(jsonify({"error":"Campaign does not exist"}),404)
        wallet_id=existing_campaign.walletId
        try:
            response = service.wallets.fund(wallet_id=wallet_id, email=email, phone_number=phoneNumber,
                                            amount=float(amount), currency="KES", narrative=f"Donation for {existing_campaign.campaignName}", 
                                            mode="MPESA-STK-PUSH")
            
            # print(response)
            data = response
            if data.get("errors"):
                error_message = data.get("errors")[0].get("detail")
                return  make_response(jsonify({"message":error_message}))
            # return jsonify(data)
            new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, status= data.get('invoice').get('state'), invoice_id= data.get('invoice').get('invoice_id'))
            
            db.session.add(new_donation)
            db.session.commit()
            return make_response(jsonify({"message": "Donation initialised successfully!", "data": new_donation.serialize()}), 200)
            # else:
            #     return make_response(jsonify({'error':'Error making donation'}), 400)
        except TypeError as ex:
            print(ex)
            return make_response(jsonify({"error":f"An error occured:{e}"}))
        except ValueError:
            return make_response(jsonify({"error": "Invalid value"}),400)  
        except Exception as e:
            print (e)
            if e:
                return make_response(jsonify({"error": f"Unexpected Error: {str(e)}"}), 400)

class Donate(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"error": "User not found"}, 404
        all_donations = Donation.query.filter_by(user_id=user.id).all()
        if not all_donations:
            return {"error": "No donations found"}, 404
        response_dict = [donation.serialize() for donation in all_donations]
        response = make_response(jsonify(response_dict),200)
        return response
       

    @jwt_required()
    def post(self):
        current_user= get_jwt_identity()
        user = User.query.filter_by(username=current_user).first()
        if not user:
            return {"error": "User not found"}, 404
        data= request.get_json()
        amount= data.get('amount')
        campaign_id= data.get('campaignId')

        if not amount:
            return make_response(jsonify({"error":"Amount is required."}),400)
        if int(amount) <5:
                return make_response(jsonify({"error":"Donation must be above Kshs 5."}),400)

        try:
            existing_campaign= Campaign.query.get(campaign_id)
            if not existing_campaign:
                return {"error":"Campaign does not exist"},404

            service = APIService(token=token,publishable_key=publishable_key, test=True)

            response = service.wallets.fund(wallet_id=existing_campaign.walletId, email=user.email, phone_number=user.phoneNumber,
                                            amount=amount, currency="KES", narrative="Deposit", 
                                            mode="MPESA-STK-PUSH")
            # new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, user_id=user.id)
            data = response
            if data.get("errors"):
                error_message = data.get("errors")[0].get("detail")
                return  make_response(jsonify({"message":error_message}))
            # return jsonify(data)
            try:
                new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, user_id=user.id, status= data.get('invoice').get('state'), invoice_id= data.get('invoice').get('invoice_id'))
                
                db.session.add(new_donation)
                db.session.commit()
                return make_response(jsonify({"message": "Donation initialised successfully!", "data": new_donation.serialize()}), 200)
            except  Exception as e:
                print (e)
                db.session.rollback()
                return {"error":"An error occurred while processing your donation"}
        except Exception as e:
            print (e)
            return jsonify({"error": "An error occurred while processing your request. Please try again later"}), 500


#Get all campaign transactions
@app.route('/api/v1.0/all_transactions/<int:id>', methods=['GET'])
@jwt_required()  
def wallet_transactions(id):
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.filter_by(id=current_user_id).first()
    if not existing_org:
        return  jsonify({"error":"Organisation does not exist"}),404

    #checking a if a campaign exist
    existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
    if not existing_campaign:
        return  jsonify({"error":"Campaign does not exist'"}),404
    wallet_id= existing_campaign.walletId

    url = f"https://sandbox.intasend.com/api/v1/transactions/?wallet_id={wallet_id}"
    try:
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " +token
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("errors"):
            error_message = data.get("errors")
            return make_response(jsonify({"error":error_message}),400)
        return jsonify(data.get("results")), 200
        
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request"}),500

# Get campaign transactions filters
@app.route('/api/v1.0/filter_transactions/<int:id>', methods=['POST'])
# @jwt_required()  
def wallet_transactions_filters(id):
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.get(current_user_id)
    if not existing_org:
        return  jsonify({"error":"Organisation does not exist"}),401
    
    data= request.get_json()
    trans_type= data.get('trans_type')
    start_date=data.get('start_date')
    end_date=data.get('end_date')

    existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
    if not existing_campaign:
        return  jsonify({"error":"Campaign does not exist'"}),404
    wallet_id= existing_campaign.walletId

    if trans_type:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?trans_type={trans_type}&wallet_id={wallet_id}"
    if  start_date and trans_type:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?trans_type={trans_type}&wallet_id={wallet_id}Q&start_date={start_date}"
    if start_date and end_date:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?wallet_id={wallet_id}&start_date={start_date}&end_date={end_date}"
    if trans_type and end_date:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?trans_type={trans_type}&wallet_id={wallet_id}&end_date={end_date}"
    if trans_type and start_date and end_date:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?trans_type={trans_type}&wallet_id={wallet_id}&start_date={start_date}&end_date={end_date}"
    if end_date:
        url = f"https://sandbox.intasend.com/api/v1/transactions/?wallet_id={wallet_id}&end_date={end_date}"
    try:
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " +token
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("errors"):
            error_message = data.get("errors")
            return make_response(jsonify({"error":error_message}),400)
        return jsonify(data.get("results")), 200
        
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request"}),500

#Route to send email to us in the contact form
@app.route("/api/v1.0/contact_form", methods=["POST"])
def contact_us():
    data = request.get_json()
    name = data.get("name")
    subject = data.get("subject")
    message = data.get("message")
    from_email = data.get("from_email")
    recipients = ["msaadacontact@gmail.com"]

    if  not all([name,subject,message,from_email]):
       return jsonify({"error":"Missing required field(s)"}),400
    try:    
        msg = Enquiry(name=name,email=from_email, subject=subject, message=message)
        db.session.add(msg)
        db.session.commit()
        sendMail.send_enquiry_mail(recipients,message,subject,from_email,name)
        return  jsonify({"message":"Your message has been received and will be responded to shortly."}),200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error":f"Email already exists in our database.\n {str(e)}"}),400


# forgot password reset
@app.route('/api/v1.0/forgot_password', methods=['POST'])
def forgot_password():
    email = request.json.get('email')
    user = User.query.filter_by(email=email).first()
    if user is None:
        return jsonify({"error": "No account associated with this email found!"}), 404
    else:
        otp = OTPGenerator.generate_otp()
        app.config['OTP_STORAGE'][email] = otp
        OTPGenerator.send_otp(email, otp)
        return jsonify({'message': 'OTP sent to your email'}), 200

# verify OTP and update password
@app.route('/api/v1.0/reset_password', methods=['PATCH'])
def reset_password():
    email = request.json.get('email')
    otp_entered = request.json.get('otp')
    new_password = request.json.get('new_password')

    user = User.query.filter_by(email=email).first()

    if user and email in app.config['OTP_STORAGE'] and app.config['OTP_STORAGE'][email] == otp_entered:
        user.password = new_password
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
    else:
        return jsonify({'error': 'Invalid OTP or email'}), 400

#organisation forget password   
@app.route('/api/v1.0/org_forgot_password', methods=['POST'])
def org_forgot_password():
    orgEmail = request.json.get('email')
    organisation = Organisation.query.filter_by(orgEmail=orgEmail).first()
    if organisation is None:
        return jsonify({"error": "No account associated with this email found!"}), 404
    else:
        otp = OTPGenerator.generate_otp()
        app.config['OTP_STORAGE'][orgEmail] = otp
        OTPGenerator.send_otp(orgEmail, otp)
        return jsonify({'message': 'OTP sent to your email'}), 200

# verify OTP and update password
@app.route('/api/v1.0/org_reset_password', methods=['PATCH'])
def org_reset_password():
    orgEmail = request.json.get('email')
    otp_entered = request.json.get('otp')
    new_password = request.json.get('new_password')

    organisation = Organisation.query.filter_by(orgEmail=orgEmail).first()

    if organisation and orgEmail in app.config['OTP_STORAGE'] and app.config['OTP_STORAGE'][orgEmail] == otp_entered:
        organisation.password = new_password
        
        db.session.commit()
        
        return jsonify({'message': 'Password reset successfully'}), 200
    else:
        return jsonify({'error': 'Invalid OTP or email'}), 400


api.add_resource(userData, '/api/v1.0/users')
api.add_resource(userDataByid, '/api/v1.0/usersdata')
api.add_resource(campaignData, '/api/v1.0/campaigns')
api.add_resource(campaignById, '/api/v1.0/org_campaigns')    
api.add_resource(addAccount, '/api/v1.0/accounts')
api.add_resource(accountById , '/api/v1.0/orgaccounts')
api.add_resource(Organization, '/api/v1.0/organisations')
api.add_resource(OrganisationDetail, '/api/v1.0/organisation')
api.add_resource(Donate, '/api/v1.0/user/donations')
api.add_resource(ExpressDonations, '/api/v1.0/express/donations')


if __name__  =="__main__":
    app.run (port =5555, debug =True)