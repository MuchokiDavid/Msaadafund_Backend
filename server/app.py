#Flask app
from flask import Flask, request,jsonify,make_response,Response
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation,Account,TokenBlocklist, Enquiry,Transactions,Subscription, TransactionApproval, Signatory
from utility import check_wallet_balance, sendMail, OTPGenerator
import os
from dotenv import load_dotenv
load_dotenv()
from intasend import APIService
import uuid
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt
import requests
from datetime import datetime, date
from flask_jwt_extended import JWTManager,jwt_required,get_jwt_identity
from flask_mail import Mail
from auth import auth_bp
# from views import view_bp
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from views import UserAdminView,DonationAdminView,CampaignAdminView,OrganisationAdminView,AccountAdminView, TransactionAdminView,SignatoriesadminView
from cloudinary.uploader import upload
import cloudinary.api
import random
import string
from flask_cors import CORS
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4,legal
from reportlab.lib.units import inch
import io
import re
import textwrap
import tempfile
from sqlalchemy.exc import IntegrityError
from intasendrequests import buy_airtime,pay_to_paybill,pay_to_till,withdraw_to_bank,withdraw_to_mpesa



#fetch environment variables  for the api key and server url
token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
main_pocket= os.getenv('MAIN_WALLET')
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
CORS(app)
# admin.init_app(app)
api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager()
jwt.init_app(app)
mail = Mail(app)


cloudinary.config( 
  cloud_name = os.getenv('CLOUDINARY_NAME'),
  api_key = os.getenv('CLOUDINARY_API_KEY'), 
  api_secret = os.getenv('CLOUDINARY_SECRET_KEY')
)

# register blueprint
app.register_blueprint(auth_bp, url_prefix='/api/v1.0/auth')
# register views
# app.register_blueprint(view_bp, url_prefix ='/auths')

#============================FLask admin panel routes ======================================

# Register the models with Flask-Admin
admin.add_view(UserAdminView(User, db.session))
admin.add_view(CampaignAdminView(Campaign, db.session))
admin.add_view(DonationAdminView(Donation, db.session))
admin.add_view(OrganisationAdminView(Organisation, db.session))
admin.add_view(AccountAdminView(Account, db.session))
admin.add_view(ModelView(TokenBlocklist, db.session))
admin.add_view(TransactionAdminView(Transactions, db.session))
admin.add_view(SignatoriesadminView(Signatory, db.session))

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



#===============================User model routes==============================================================

# classes for users
class userData (Resource):
    def get(self):
        users = [user.serialize() for user in User.query.filter_by(isActive = True).all()]
        response = make_response(jsonify(users), 200)
        return response
  
#Get user by id
class userDataByid(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user, isActive=True).first()
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
        nationalId = data.get('nationalId')

        existing_user = User.query.filter_by(id = current_user).first()
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
        if nationalId:
            existing_user.nationalId = nationalId
        if 'isActive' in data:
            existing_user.isActive = data['isActive']

        db.session.commit()

        response = make_response(jsonify(existing_user.serialize()),200)
        return response
  
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return jsonify({'error':"User not found"}), 404
        else:
            user.isActive = False       
            # db.session.delete(user)
            db.session.commit()

            return {"message": "User deactivated successfully"},200   
        
#===============================subscription  routes==============================================================
@app.route('/api/v1.0/subscription_status',methods=['GET'])
@jwt_required()
def get_subscription():
    current_user = get_jwt_identity()
    user = User.query.filter_by(id=current_user).first()
    if not user:
        return {"error":"User not found"}, 404
    subscriptions = Subscription.query.filter_by(user_id=user.id).all()
    if not subscriptions:
        return {"error":"No subscription found"}, 404
    response_dict = [sub.serialize() for sub in subscriptions]
    response = make_response(jsonify(response_dict), 200)
    return response

class GetSubscription(Resource):
    @jwt_required()
    def get(self,org_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return {"error":"User not found"}, 404
        subscriptions = Subscription.query.filter_by(user_id=user.id, organisation_id=org_id).first()
        if not subscriptions:
            return {"error":"No subscription found"}, 404
        # response_dict = [sub.serialize() for sub in subscriptions]
        response_dict = subscriptions.serialize()
        response = make_response(jsonify(response_dict), 200)
        return response
    
    @jwt_required()
    def post(self,org_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return {"error":"User not found"}, 404
        
        org = Organisation.query.filter_by(id=org_id).first()
        if not org:
            return {"error":"Organisation not found"}, 404
        org_name = org.orgName
        available_subscription = Subscription.query.filter_by(user_id=user.id, organisation_id=org_id).first()
        if available_subscription:
            return {"error":"Subscription already exists"}, 404
        
        
        new_subs = Subscription(user_id=user.id, organisation_id=org_id)
    
        db.session.add(new_subs)
        db.session.commit()
        sendMail.send_subscription_email(user.email, user.firstName, org_name)

        response = make_response(jsonify(new_subs.serialize()), 200)
        return response
    
    @jwt_required()
    def delete(self, org_id):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return {"error":"User not found"}, 404
        available_subscription = Subscription.query.filter_by(user_id=user.id, organisation_id=org_id).first()
        if not available_subscription:
            return {"error":"Subscription not found"}, 404
        db.session.delete(available_subscription)
        db.session.commit()

        return {"message": "Subscription deleted successfully"},200
        
# Get all subscriptions in an organisation to show on org dashboard
class OrgSubscriptions(Resource):
    @jwt_required()
    def get(self):
        current_user= get_jwt_identity()
        existing_org= Organisation.query.filter_by(id=current_user).first()
        if not existing_org:
            return jsonify({"error":"Organisation does not exist."}),404
        all_subscriptions= Subscription.query.filter_by(organisation_id=existing_org.id).all()
        response_dict = [sub.serialize() for sub in all_subscriptions]
        response = make_response(jsonify({'message':response_dict}), 200)    
        return response             
        
#===============================Campaign model routes==============================================================

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
    youtube_link = request.form.get('youtubeLink')
    
    # Fetch organization by current user ID
    available_org = Organisation.query.filter_by(id=current_user).first()
    if not available_org:
        return jsonify({"error": "Organisation does not exist."}), 404

    # Convert date strings to Python date objects
    startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
    endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()
    current_date = datetime.now().date()

    # Validate dates
    if startDate < current_date:
        return jsonify({'error': 'cannot create a campaign in the past'}), 400 
    if endDate < current_date:
        return jsonify({'error': 'end date should be greater than current date'}), 400  
    if endDate < startDate:
        return jsonify({'error': 'end date cannot be before start date'}), 400
 
    if not (campaignName and description and startDate and endDate):
        return jsonify({"error": "Please provide complete information"}), 400
    
    isActive = startDate >= current_date

    # Check for existing active campaigns and campaign name duplication
    all_campaigns = Campaign.query.filter_by(org_id=available_org.id).all()
    available_campaigns = [c for c in all_campaigns if c.isActive]

    if any(c.campaignName == campaignName for c in available_campaigns):
        return jsonify({"error": "Campaign with this name already exists"}), 400

    # Upload the banner image to Cloudinary and create a new campaign
    try:
        result = upload(banner)
        if "secure_url" not in result:
            return jsonify({"error": "Failed to upload banner to Cloudinary"}), 404

        new_campaign = Campaign(
            campaignName=campaignName,
            description=description,
            category=category,
            youtube_link=youtube_link,
            banner=result["secure_url"],
            startDate=startDate,
            endDate=endDate,
            targetAmount=float(targetAmount),
            isActive=isActive,
            org_id=available_org.id
        )

        # Create wallet
        try:
            response = service.wallets.create(currency="KES", label=str(uuid.uuid4()), can_disburse=True)
            if response.get('errors'):
                error_message = response.get("errors")[0].get("detail")
                return jsonify({'error': error_message})

            new_campaign.walletId = response.get("wallet_id")
        except Exception as e:
            return jsonify({"error": str(e)}), 404

        # Save campaign to database
        try:
            db.session.add(new_campaign)
            db.session.commit()

            sendMail.send_post_campaign(available_org, campaignName, description, category, targetAmount, startDate, endDate)
            
            # Notify subscribed users
            users_subscribed = Subscription.query.filter_by(organisation_id=available_org.id).all()
            for user in users_subscribed:
                user_detail = User.query.get(user.user_id)
                sendMail.send_subscribers_createCampaign(
                    user_detail.email, user_detail.firstName, new_campaign.campaignName,
                    new_campaign.description, new_campaign.startDate, new_campaign.endDate,
                    new_campaign.targetAmount, available_org.orgName
                )

        except Exception as e:
            return jsonify({"error": "Something went wrong while creating your campaign"}), 500

        return jsonify({"message": new_campaign.serialize()}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 404

#get campaigns
class campaignData(Resource):
    # @jwt_required()
    def get(self):
        page = request.args.get('page', default=1, type=int)
        per_page = request.args.get('per_page', default=12, type=int)
        campaigns = Campaign.query.filter_by(isActive=True).paginate(page=page, per_page=per_page)
        data = [campaign.serialize() for campaign in campaigns.items]
        response = make_response(jsonify(data), 200)
        return response

#Get all campaigns without pagination
@app.route('/api/v1.0/get_all_campaigns', methods=['GET'])
def get_all_campaigns():
    try:
        campaigns = Campaign.query.order_by(Campaign.created_at.desc()).all()
        output = []
        for campaign in campaigns:
            campaign_dict = campaign.serialize()
            output.append(campaign_dict)
        return jsonify(output)
    except Exception as e:
        return {'error': 'Error getting all campaigns: {}'.format(str(e))}, 500
    
#Get all campaigns  by organization id
class OrgCampaigns(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        campaigns = Campaign.query.filter_by(org_id=current_user, isActive=True).all()
        if not campaigns:
            return {"error":"Campaign not found"}, 404
        return make_response(jsonify({'campaigns':[camp.serialize() for camp in campaigns]}), 200)

#Get inactive campaigns
@app.route('/api/v1.0/get_inactive', methods=['GET'])
@jwt_required()
def  getInactiveCampaign():
    try:
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id=current_user).first().id
        if not org:
            return {"error":"Organisation not found"}, 404
        campaign = Campaign.query.filter_by(org_id=current_user, isActive=False).all()
        if not campaign:
            return {"error":"Inactive Campaign not found"}, 404
        data = [c.serialize() for c in campaign]
      
        response = make_response(jsonify(data), 200)
        return response
    except Exception as e:
        return {"error":str(e)}
   

# path inactive campaigns
@app.route("/api/v1.0/activate/campaign/<int:campaignId>", methods=["PATCH"])
@jwt_required()
def activateCampaign(campaignId):
    try:
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id=current_user).first()
        if not org:
            return {"error":"Organisation not found"}, 404
        campaign = Campaign.query.filter_by(id=campaignId,org_id=current_user).first()
        if not campaign:
            return {"error":"Inactive Campaign not found"}, 404
        campaign.isActive = True
        db.session.commit()
        # return that campaign
        response = make_response(jsonify(campaign.serialize()))
        return response

    except Exception as e:
        return {"error":str(e)}



#---------------------------------------Get featured campaigns---------------------------------------------
@app.route('/api/v1.0/featured', methods= ['GET'])
def featured_campaigns():
    try:
        today = date.today().isoformat()
        all_campaigns = Campaign.query.filter_by(isActive=True, featured=True).filter(Campaign.endDate > today).all()
        # all_campaigns= Campaign.query.filter_by(isActive=True, featured=True).filter(Campaign.endDate>today).all()
        featured_campaigns = [campaign.serialize() for campaign in all_campaigns]
        if len(featured_campaigns)>=4:
            random_campaigns = random.sample(featured_campaigns, 4)
            response = make_response(jsonify(random_campaigns), 200)
            return response
        else:
            response= make_response(jsonify(featured_campaigns), 200)
            return response
    except  Exception as e:
        print("Error occured : ",e)
        return jsonify({"error": "An error occurred while retrieving the featured campaigns."})

@app.route('/campaigns/<int:campaign_id>/feature', methods=['POST'])
def feature_campaign(campaign_id):
    try:
        campaign = Campaign.query.get_or_404(campaign_id)
        campaign.featured = True
        db.session.commit()
        return jsonify({"message": "Campaign featured successfully."}), 200
    except Exception as e:
        print("Error occured : ", e)
        return jsonify({"error": "An error occurred while retrieving the featured campaigns."})

@app.route('/campaigns/<int:campaign_id>/unfeature', methods=['POST'])
def unfeature_campaign(campaign_id):
    try:
        campaign = Campaign.query.get_or_404(campaign_id)
        campaign.featured = False
        db.session.commit()
        return jsonify({"message": "Campaign unfeatured successfully."}), 200
    except Exception as e:
        print("Error occured : ", e)
        return jsonify({"error": "An error occurred while retrieving the featured campaigns."})
    
#-----------------------------------------------------------------------------------------------------------------

#Get one campaign by id in unprotected route
@app.route("/api/v1.0/campaign/<int:campaignId>", methods=["GET"])
def readOne(campaignId):
    """Get the details of one specific campaign."""
    try:
        campaign = Campaign.query.get(campaignId)
    except Exception as e:
        print(e)
        return jsonify({"error":f"Invalid campaign ID: {campaignId}"}), 400

    # Return the serialized campaign
    return jsonify(campaign.serialize())


# patch campaign by specific id
@app.route("/api/v1.0/updatecampaign/<int:campaignId>", methods=["PATCH"])
@jwt_required()
def updateOne(campaignId):
    try:
        description = request.form.get('description')
        banner = request.files.get('banner') 
        startDateStr = request.form.get('startDate')
        endDateStr = request.form.get('endDate')    
        youtube_link = request.form.get('youtubeLink')

        current_user = get_jwt_identity()
        
        existing_campaign = Campaign.query.filter_by(id=campaignId, org_id=current_user).first()
        if not existing_campaign:
            return {"error":"Campaign not found"}, 404
        if description:
            existing_campaign.description = description
        if youtube_link:
            existing_campaign.youtube_link = youtube_link
        if banner:

            # Delete the existing banner from Cloudinary
            if existing_campaign.banner:
                public_id = existing_campaign.banner.split('/')[-1].split('.')[0]
                try:
                    # Delete the image using the public_id
                    res = cloudinary.uploader.destroy(public_id)
                    print(f"Delete response: {res}")
                    if res.get('result') == 'ok':
                        print("Image deleted successfully.")
                    else:
                        print("Failed to delete the image.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            # Upload the new banner to Cloudinary
            result = upload(banner)
            if "secure_url" in result:
                existing_campaign.banner = result["secure_url"]
        try:
            if startDateStr:
                startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
                existing_campaign.startDate = startDate
            if endDateStr:
                endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()
                existing_campaign.endDate = endDate
            
            current_date = datetime.now().date()
            # if startDate < current_date:
            #     return {'error': 'cannot create a campaign in the past'}, 400
            if endDate < current_date:
                return {'error':'enddate  should be greater than current date'} ,400  
            if endDate < startDate:
                return {'error': 'end date cannot be before start date'}, 400
        except Exception as e:
            return {"error":str(e)}
    
        
        db.session.commit()

        response = make_response(jsonify(existing_campaign.serialize()), 200)
        return response
    except Exception as e:
        print(e)
        return {"error":str(e)}

# delete campaign
@app.route("/api/v1.0/deletecampaign/<int:campaignId>", methods=["DELETE"])
@jwt_required()
def delete(campaignId):
    current_user = get_jwt_identity()
    organisation = Organisation.query.filter_by(id=current_user).first()
    
    if not organisation:
        return jsonify({'error':"Organisation not found"}), 404
    
    existing_campaign = Campaign.query.filter_by(id=campaignId, org_id=current_user).first()
    if not existing_campaign:
        return jsonify({'error':"Campaign not found"}), 404
    else:
        existing_campaign.isActive = False       
        # db.session.delete(campaign)
        db.session.commit()
        # return that campaign
        response = make_response(jsonify(existing_campaign.serialize()),200)
        # return {"message": "Campaign deactivated successfully",
        #         "data":response                
        #     }
        return response

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
    
    # @jwt_required()
    # def patch (self):
    #     data=request.get_json()
    #     description = data.get('description')
    #     endDate = data.get('endDate')
    #     targetAmount = data.get('targetAmount')

    #     current_user = get_jwt_identity()
    #     existing_campaign = Campaign.query.filter_by(org_id=current_user).first()
    #     if not existing_campaign:
    #         return {"error":"Campaign not found"}, 404
    #     if description:
    #         existing_campaign.description = description
    #     if endDate:
    #         existing_campaign.endDate =endDate
    #     if targetAmount:
    #         existing_campaign.targetAmount = float(targetAmount)

    #     db.session.commit()

    #     response = make_response(jsonify(existing_campaign.serialize()), 200)
    #     return response

    # @jwt_required()
    # def delete(self):
    #     data=request.get_json()
    #     current_user = get_jwt_identity()
    #     organisation = Organisation.query.filter_by(id=current_user).first()
        
    #     if not organisation:
    #         return jsonify({'error':"Organisation not found"}), 404
        
    #     existing_campaign = Campaign.query.filter_by(campaignName=data['name']).first()
    #     if not existing_campaign:
    #         return jsonify({'error':"Campaign not found"}), 404
    #     else:
    #         existing_campaign.isActive = False       
    #         # db.session.delete(campaign)
    #         db.session.commit()

    #         return {"message": "Campaign deactivated successfully"},200   

#===================================Intasend balance API=====================================================
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
    # print(wallet_id)
    try:
        response = service.wallets.details(wallet_id)
        # print(response)
        if response.get("errors"):
            error_message = response.get("errors")
            return  make_response({ "error":error_message} , 400)

        return jsonify({'wallet_details': response}), 200
    except Exception as e:
        return jsonify({ "error":"Internal server error"}), 400
    
#==================================Account model routes==============================================================
    
class addAccount(Resource):
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
            return {"error": "Organisation not found"}, 400
        
        data = request.get_json()
        if not data or 'providers' not in data or 'accountNumber' not in data or 'pin' not in data:
            return {"error": "Invalid JSON data"}, 400

        providers = data.get('providers')
        accountName = data.get('accountName')
        accountNumber = data.get('accountNumber')
        bank= data.get('bank')
        bank_code= data.get('bankCode')
        hashed_pin = data.get('pin')
        email = existing_organisation.orgEmail 
        orgName = existing_organisation.orgName

        # Check if the account number already exists
        existing_account = Account.query.filter_by(accountNumber=accountNumber).first()
        if existing_account:
            return {"error": "Account number already exists"}, 400

        try:
            new_account = Account(providers=providers, bank=bank, bank_code=bank_code, accountName=accountName, accountNumber=accountNumber, pin=hashed_pin, orgId=existing_organisation.id)
            db.session.add(new_account)
            db.session.commit()
            sendMail.send_user_signup_account(email, new_account.providers, new_account.accountNumber, orgName)
            return ({
                "message": "Account registered successfully",
                "user": new_account.serialize()
            }), 200
        except Exception as e:
            return ({"error": "Failed to create account"}), 500

#Get account by id
class accountById(Resource):
    @jwt_required()
    def delete(self,id):
        # data = request.get_json()
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error":"Organisation not found"}, 404
        try:
            account = Account.query.filter_by(id=id).first()
            if not account:
                return {"error":"Account not found"}, 404
            db.session.delete(account)
            db.session.commit()

            return {"message": "Account deleted successfully"},200  
        except Exception as e:
            return  

#===============================Account pin routes==============================================================

# User forgot password reset
@app.route('/api/v1.0/account_pin', methods=['POST'])
@jwt_required()
def account_pin():
    current_user = get_jwt_identity()
    orgEmail = request.json.get('email')
    organisation = Organisation.query.filter_by(orgEmail=orgEmail, id=current_user).first()
    if organisation is None:
        return jsonify({"error": "No account associated with this email found!"}), 404
    else:
        otp = OTPGenerator.generate_otp()
        app.config['OTP_STORAGE'][orgEmail] = otp
        OTPGenerator.send_account_otp(orgEmail, otp)
        return jsonify({'message': 'OTP sent to your email'}), 200
    
@app.route('/api/v1.0/confirm_account_pin', methods=['PATCH'])
@jwt_required()
def confirm_accountotp():
    current_user = get_jwt_identity()
    orgEmail = request.json.get('email')
    otp_entered = request.json.get('otp')
    org  = Organisation.query.filter_by(orgEmail=orgEmail, id=current_user).first()
    if not org:
        return jsonify({'error': 'Organisation not found'}), 404

    if not orgEmail or not otp_entered:
        return jsonify({'error': 'Email and OTP are required'}), 400

    if org and orgEmail in app.config['OTP_STORAGE'] and app.config['OTP_STORAGE'][orgEmail] == otp_entered:
        # Clear the OTP after successful verification
        del app.config['OTP_STORAGE'][orgEmail]
        return jsonify({'message': f'Welcome to your account {org.orgName}!'}), 200
    else:
        return jsonify({'error': 'Invalid OTP, Generate a new one'}), 400

#====================================Organisation by id routes==============================================================
@app.route('/api/v1.0/org_by_id/<string:orgName>', methods=['GET'])
def org_by_id(orgName):
    organisation= Organisation.query.filter_by(orgName=orgName, isVerified=True).first()
    if not organisation:
        return {"error":"Organisation not found"}, 404
    
    response=make_response(jsonify(organisation.serialize()))
    return response
    

#====================================Organisation model routes==============================================================
class Organization(Resource):
    def get(self):
        organizations = Organisation.query.filter_by(isVerified=True).all()
        serialized_organizations = [org.serialize() for org in organizations]
        response = make_response(jsonify(serialized_organizations), 200)
        return response

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
        orgName = request.form.get('orgName')
        # orgEmail = request.form.get('orgEmail')
        orgPhoneNumber = request.form.get('orgPhoneNumber')
        orgAddress = request.form.get('orgAddress')
        orgDescription = request.form.get('orgDescription')
        youtube_link = request.form.get('youtube_link')
        orgType = request.form.get('orgType')
        website_link = request.form.get('website_link')
        profileImage = request.files.get('profileImage')

        existing_org = Organisation.query.filter_by(id=current_user).first()
        if not existing_org:
            return {"error": "Organisation does not exist"}, 404
        try:
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
            if youtube_link:
                existing_org.youtube_link = youtube_link
            if orgType:
                existing_org.orgType = orgType
            if website_link:
                existing_org.website_link = website_link
            if profileImage:
                public_id = existing_org.profileImage.split('/')[-1].split('.')[0]
                try:
                    # Delete the image using the public_id
                    res = cloudinary.uploader.destroy(public_id)
                    print(f"Delete response: {res}")
                    if res.get('result') == 'ok':
                        print("Image deleted successfully.")
                    else:
                        print("Failed to delete the image.")
                except Exception as e:
                    print(f"An error occurred: {e}")
                    
                result = upload(profileImage)
                if "secure_url" in result:
                    existing_org.profileImage = result["secure_url"]
            db.session.commit()

            response= make_response(jsonify({"message": "Organisation has been updated", "Data": existing_org.serialize()}))
            # return {"message": "Organisation has been updated", "Data": existing_org.serialize()}
            return response
        except Exception as e:
            print(e)
            return {"error":str(e)}, 500

# ===================================Signatories routes================================================================
class Signatories(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error": "Organisation not found"}, 404

        signatories = Signatory.query.filter_by(org_id=existing_organisation.id).all()
        if not signatories:
            return {"error": "Signatories not found"}, 404

        serialized_signatories = [signatory.serialize() for signatory in signatories]
        response  = make_response(jsonify(serialized_signatories),200)
        return response
       
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error": "Organisation not found"}, 404

        data= request.get_json()
        email = data.get('email')
        role = data.get('role')

        existing_user = User.query.filter_by(email=email).first()
        if not existing_user:
            return {"error": "User not registered"}, 404

    
        all_signataries = Signatory.query.filter_by(org_id=existing_organisation.id).all()
        if len(all_signataries) >5:
            return {"error": "Maximum number of signatories reached"}, 400
        
        existing_signatory = Signatory.query.filter_by(user_id=existing_user.id, org_id=existing_organisation.id).first()
        if existing_signatory:
            return {"error": "Signatory already exists"}, 400

        existing_orders = [signatory.order for signatory in all_signataries]
        order = 1
        while order in existing_orders:
            order += 1


        new_signatory = Signatory(user_id=existing_user.id,role=role, org_id=existing_organisation.id,order=order)

        db.session.add(new_signatory)
        db.session.commit()
        response = make_response(jsonify({'message':new_signatory.serialize()}))

        sendMail.send_signatory_email(existing_user.email,existing_user.firstName,existing_organisation.orgName)
        sendMail.send_signatory_add( existing_user.firstName,existing_organisation.orgName, existing_organisation.orgEmail)

        return response
            
            
class SignatoryDetail(Resource):
    @jwt_required()
    def get(self, id):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error": "Organisation not found"}, 404

        signatory = Signatory.query.filter_by(id=id, org_id=existing_organisation.id).first()
        if not signatory:
            return {"error": "Signatory not found"}, 404

        return make_response(jsonify(signatory.serialize()))
    
    @jwt_required()
    def delete(self, id):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error": "Organisation not found"}, 404

        try:
            signatory = Signatory.query.filter_by(id=id, org_id=existing_organisation.id).first()
            if not signatory:
                return {"error": "Signatory not found"}, 404
            user = User.query.filter_by(id=signatory.user_id).first()
            if not user:
                return {"error": "User not found"}, 404      
            
            TransactionApproval.query.filter_by(signatory_id=id).delete()

            db.session.delete(signatory)
            db.session.commit()
            sendMail.send_signatory_email_removal(user.email, user.firstName, existing_organisation.orgName)
            return {"message": "Signatory deleted successfully"}, 200
        
        except IntegrityError as e:
            db.session.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except Exception as e:
            db.session.rollback()
            return {"error": f"Unexpected error: {str(e)}"}, 500
    
    @jwt_required()
    def patch(self, id):
        current_user = get_jwt_identity()
        existing_organisation = Organisation.query.filter_by(id=current_user).first()
        if not existing_organisation:
            return {"error": "Organisation not found"}, 404
        
        try:
            signatory = Signatory.query.filter_by(id=id, org_id=existing_organisation.id).first()
            if not signatory:
                return {"error": "Signatory not found"}, 404

            data = request.get_json()
            role = data.get('role')

            if role:
                signatory.role = role
            db.session.commit()
            # get response
            response  = make_response(jsonify(signatory.serialize()),201)
            return response

        except Exception as e:
            return {"error":str(e)}, 500
    
#=====================================Intasend sdk routes==============================================================

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

# Route to withdraw money to M-pesa number-----------------------------------
@app.route("/api/v1.0/withdraw",methods=["POST"])
@jwt_required()
def campaign_money_withdrawal():
    current_user = get_jwt_identity()
    organisation = Organisation.query.filter_by(id=current_user).first()
    if not organisation:
         return {"error":"organisation cannot be found"},404
    
    data=request.get_json()
    providers= data.get("providers")# KCB, M-Pesa, Equity,Family bank, etc
    accountNumber= data.get("accountNumber")#bank account number and mpesa phone number
    amount=float(data.get('amount'))
    # orgId= int(data.get('orgId'))# use jwt_identity
    campaign=int(data.get("campaign"))
    pin= data.get("pin")
    
    account= Account.query.filter_by(providers=providers,accountNumber=accountNumber,orgId=organisation.id).first()
    if account is None:
        return jsonify({"error": "No such account"}),404
    
    if not bcrypt.check_password_hash(account.hashed_pin, pin):
        return jsonify({'error': 'Invalid pin'}), 401 

    campaigns= Campaign.query.filter_by(id=campaign, org_id=organisation.id, isActive=True).first()
    if not campaigns:
        return jsonify({"error":"Campaign does not exist or inactive."}),404
    
    signatories = Signatory.query.filter_by(org_id=organisation.id).all()
    if len(signatories) < 1:
        return jsonify({"error": "No signatories found!"}), 404
    elif len(signatories) < 3:
        return jsonify({"error": "Please register atleast three signatories to initiate a transaction."}), 400
    
    #check wallet balance
    if float(check_wallet_balance(campaigns.walletId))<float(amount):
        return jsonify({"error":"Insufficient funds in the wallet!"}),400
    try: 
        if providers=="M-Pesa":
            # #Initiate intasend M-Pesa transaction
            new_transaction=Transactions(tracking_id='Pending',
                            batch_status= 'Pending',
                            trans_type= 'Withdraw to M-Pesa',
                            trans_status= 'Pending',
                            signatory_status='Pending',
                            amount= amount,
                            transaction_account_no=accountNumber,
                            request_ref_id= 'Pending',
                            name= organisation.orgName,
                            org_id=organisation.id,
                            campaign_name= campaigns.campaignName
                        )
                
            db.session.add(new_transaction)
            db.session.commit()

            # send mail to signatory
            for signatory in signatories:
                user = User.query.filter_by(id=signatory.user_id).first() 
                new_approval = TransactionApproval(transaction_id=new_transaction.id, signatory_id=signatory.id)
                db.session.add(new_approval)
                db.session.commit()

                sendMail.send_approval_message(user.firstName,user.email,organisation.orgName,amount,new_transaction.trans_type,account)

            return jsonify({"message": "Your transaction was created and is awaiting approval."}), 200
        
        elif providers=="Bank":
            bank= data.get("bank_code")
            #Initiate intasend bank transaction
            try:
                new_transaction=Transactions(tracking_id='Pending',
                                batch_status= 'Pending',
                                trans_type= 'Withdraw to bank',
                                trans_status= 'Pending',
                                signatory_status='Pending',
                                amount= amount,
                                transaction_account_no=accountNumber,
                                request_ref_id= 'Pending',
                                name= organisation.orgName,
                                org_id=organisation.id,
                                campaign_name= campaigns.campaignName,
                                bank_code= bank
                            )
                db.session.add(new_transaction)
                db.session.commit()

                # send mail to signatory
                for signatory in signatories:
                    user = User.query.filter_by(id=signatory.user_id).first() 
                    new_approval = TransactionApproval(transaction_id=new_transaction.id, signatory_id=signatory.id)
                    db.session.add(new_approval)
                    db.session.commit()

                    sendMail.send_approval_message(user.firstName,user.email,organisation.orgName,amount,new_transaction.trans_type,account)

                return jsonify({"message": "Your transaction was created and is awaiting approval."}), 200
                  
            except Exception as e:
                print(e)
                return jsonify({"error":str(e)}),500       
        else:
            return jsonify({"error":"select transaction"}),400
    except Exception as e :
        print(e)
        return jsonify({"error":str(e)}),500

#Route to buy airtime from a campaign
@app.route("/api/v1.0/buy_airtime",methods=["POST"])
@jwt_required()
def campaign_buy_airtime():
    current_user = get_jwt_identity()
    organisation = Organisation.query.filter_by(id=current_user).first()
    if not organisation:
        return {"error":"organisation cannot be found"},404

    data=request.get_json()
    name= data.get("name")
    amount= float(data.get("amount"))
    phone_number= data.get("phone_number")
    campaign= data.get("campaign")

    current_campaign= Campaign.query.filter_by(id=campaign, org_id=organisation.id, isActive=True).first()
    if not current_campaign:
        return jsonify({"error":"Campaign does not exist or inactive."}),404

    #check wallet balance
    wallet_id = current_campaign.walletId
    wallet_details = check_wallet_balance(wallet_id)
    if float(wallet_details) < float(amount):
            return jsonify({"error": "Insufficient funds!"}), 400
    
    signatories = Signatory.query.filter_by(org_id=organisation.id).all()
    if len(signatories) < 1:
        return jsonify({"error": "No signatories found!"}), 404
    elif len(signatories) < 3:
        return jsonify({"error": "Please register atleast three signatories to initiate a transaction."}), 400
    
    new_transaction=Transactions(tracking_id='Pending',
                                    batch_status= 'Pending',
                                    trans_type= 'Buy Airtime',
                                    trans_status= 'Pending',
                                    signatory_status='Pending',
                                    amount= amount,
                                    transaction_account_no=phone_number,
                                    request_ref_id= 'Pending',
                                    name= name,
                                    org_id=organisation.id,
                                    campaign_name= current_campaign.campaignName
                                )  
    db.session.add(new_transaction)
    db.session.commit()
    

    # send mail to signatory
    for signatory in signatories:
        user = User.query.filter_by(id=signatory.user_id).first() 
        new_approval = TransactionApproval(transaction_id=new_transaction.id, signatory_id=signatory.id)
        db.session.add(new_approval)
        db.session.commit()

        sendMail.send_approval_message(user.firstName,user.email,organisation.orgName,amount,new_transaction.trans_type,phone_number)

    return jsonify({"message": "Your transaction was created and is awaiting approval."}), 200

# get pending transactions
@app.route("/api/v1.0/pending_transactions", methods=["GET"])
@jwt_required()
def pending_transactions():
    current_user = get_jwt_identity()
    signatory = Signatory.query.filter_by(user_id=current_user).first()
    if not signatory:
        return {"error": "Unauthorized Signatory"}, 401

    transactions = Transactions.query.filter(Transactions.signatory_status.in_(['Pending', 'Awaiting'])).all()
    trans_dict = [tra.serialize() for tra in transactions]
    response = make_response(jsonify(trans_dict), 200)
    return response

# Get org approvals
@app.route("/api/v1.0/org_awaiting_approvals", methods=["GET"])
@jwt_required()
def org_awaiting_approvals():
    current_user = get_jwt_identity()
    organisation = Organisation.query.filter_by(id=current_user).first()
    if not organisation:
        return {"error": "Organisation not found"}, 404

    transactions = Transactions.query.filter(Transactions.signatory_status.in_(['Pending', 'Awaiting'])).all()
    trans_dict = [tra.serialize() for tra in transactions]
    response = make_response(jsonify(trans_dict), 200)
    return response

# ===========================Approve and Reject transactions====================================================
@app.route("/api/v1.0/approve_transaction", methods=["POST"])
@jwt_required()
def approve_transaction():
    current_user = get_jwt_identity()
    signatory = Signatory.query.filter_by(user_id=current_user).first()
    if not signatory:
        return {"error": "Unauthorized Signatory"}, 401
    
    # update transaction
    data = request.get_json()
    transaction_id = data.get("transaction_id")
    approval_status = data.get("approval_status")
    campaign_name = data.get("campaign_name")

    approval = TransactionApproval.query.filter_by(transaction_id=transaction_id, signatory_id=signatory.id).first()
    if not approval:
        return {"error": "Approval not found"}, 404

    approval.approval_status = approval_status
    approval.approval_time = datetime.now()
    db.session.commit()

    transaction = Transactions.query.filter_by(id=transaction_id).first()
    signatory_status = transaction.update_status()

    existing_campaign = Campaign.query.filter_by(campaignName=campaign_name).first()
    if not existing_campaign:
        return {"error": "Campaign not found"}, 404

    existing_organisation = Organisation.query.filter_by(id=existing_campaign.org_id).first()
    if not existing_organisation:
            return {"error": "Organisation not found"}, 404

    if signatory_status == 'Approved':
        # Send mail to notify transaction approved
        sendMail.org_approval_message(existing_organisation, transaction)        
        
        wallet_id = existing_campaign.walletId

        if transaction.trans_type == 'Buy Airtime':
            return buy_airtime(wallet_id, transaction, existing_organisation.orgName)
        elif transaction.trans_type == 'Pay to Paybill':
            return pay_to_paybill(wallet_id, transaction)
        elif transaction.trans_type == 'Withdraw to M-Pesa':
            return withdraw_to_mpesa(wallet_id, transaction)
        elif transaction.trans_type == 'Withdraw to bank':
            return withdraw_to_bank(wallet_id, transaction)
        elif transaction.trans_type == 'Pay to Till':
            return pay_to_till(wallet_id, transaction)       
        else:
            return {"error": "Invalid transaction type"}, 400
    elif signatory_status == 'Rejected':
        # Send mail to notify transaction rejected
        sendMail.org_rejected_message(existing_organisation, transaction)
        return {"error": "Transaction rejected"}, 400
    else:
        return {"message": "Approval recorded. Waiting for other signatories."}, 200


    
#Route to reject an approval
@app.route("/api/v1.0/reject_approval/<int:approval_id>", methods=["PATCH"])
@jwt_required()
def reject_approval(approval_id):
    current_user = get_jwt_identity()
    signatory = Signatory.query.filter_by(user_id=current_user).first()
    if not signatory:
        return {"error": "Unauthorized Signatory"}, 401

    approval = TransactionApproval.query.filter_by(transaction_id=approval_id, signatory_id=signatory.id).first()
    if not approval:
        return {"error": "Approval not found"}, 404

    approval.approval_status = False
    approval.approval_time = datetime.now() 
    db.session.commit()

    transaction = Transactions.query.filter_by(id=approval.transaction_id).first()
    transaction.update_status()

    existin_org= Organisation.query.filter_by(id=signatory.org_id).first()
    if not existin_org:
        return {"error": "Organisation not found"}, 404

    # Send mail to notify transaction rejected
    sendMail.org_rejected_message(existin_org,transaction)

    return {"message": "Approval rejected successfully"}, 200


# #Route to pay to a paybill from a campaign
@app.route("/api/v1.0/pay_to_paybill", methods=["POST"])
@jwt_required()
def campaign_pay_to_paybill():
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.filter_by(id=current_user_id).first()
    if not existing_org:
        return jsonify({"error": "organisation not found"}), 404

    data = request.get_json()
    name = existing_org.orgName
    account= data.get('paybillNumber')
    account_reference= data.get('accountNumber')
    # account_type= 'PayBill'
    amount = data.get('amount')
    narrative= data.get('narrative')
    campaign_id = data.get("campaignId")

    if not all([account, account_reference, amount]):
        return jsonify({"error": "Missing required fields"}), 400

    current_campaign= Campaign.query.filter_by(id=campaign_id, org_id=existing_org.id, isActive=True).first()
    wallet_id= current_campaign.walletId

    wallet_details= check_wallet_balance(wallet_id)

    if wallet_id:
        # Check the available balance of the origin wallet
        if float(wallet_details) < float(amount):
            return jsonify({"error":"Insufficient funds!"}),400
    
    signatories = Signatory.query.filter_by(org_id=existing_org.id).all()
    if len(signatories) < 1:
        return jsonify({"error": "No signatories found!"}), 404
    elif len(signatories) < 3:
        return jsonify({"error": "Please register atleast three signatories to initiate a transaction."}), 400
    
    new_transaction=Transactions(tracking_id='Pending',
                                    batch_status= 'Pending',
                                    trans_type= 'Pay to Paybill',
                                    trans_status= 'Pending',
                                    signatory_status='Pending',
                                    amount= amount,
                                    transaction_account_no=account,
                                    request_ref_id= 'Pending',
                                    name= name,
                                    acc_refence=account_reference,
                                    narrative=narrative,
                                    org_id=existing_org.id,
                                    campaign_name= current_campaign.campaignName
                                )  
    db.session.add(new_transaction)
    db.session.commit()
    

    # send mail to signatory
    for signatory in signatories:
        user = User.query.filter_by(id=signatory.user_id).first() 
        new_approval = TransactionApproval(transaction_id=new_transaction.id, signatory_id=signatory.id)
        db.session.add(new_approval)
        db.session.commit()

        sendMail.send_approval_message(user.firstName,user.email,existing_org.orgName,amount,new_transaction.trans_type,account)

    return jsonify({"message": "Your transaction was created and is awaiting approval."}), 200

# #Route to pay to a till number
@app.route("/api/v1.0/pay_to_till", methods=["POST"])
@jwt_required()
def campaign_pay_to_till():
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.get(current_user_id)
    if not existing_org:
        return jsonify({"error": "organisation not found"}), 404

    try:
        data = request.get_json()
        name = existing_org.orgName
        account= data.get('tillNumber')
        amount = data.get('amount')
        narrative= data.get('narrative')
        campaign_id = data.get("campaignId")

        if not all([account, amount]):
            return jsonify({"error": "Missing required fields"}), 400

        current_campaign= Campaign.query.filter_by(id=campaign_id, org_id=existing_org.id, isActive=True).first()
        wallet_id= current_campaign.walletId
        wallet_details= check_wallet_balance(wallet_id)
        if wallet_id:
            # Check the available balance of the origin wallet
            if float(wallet_details) < float(amount):
                return jsonify({"error":"Insufficient funds!"}),400
            
        signatories = Signatory.query.filter_by(org_id=existing_org.id).all()
        if len(signatories) < 1:
            return jsonify({"error": "No signatories found!"}), 404
        elif len(signatories) < 3:
            return jsonify({"error": "Please register atleast three signatories to initiate a transaction."}), 400
        
        new_transaction=Transactions(tracking_id='Pending',
                                        batch_status= 'Pending',
                                        trans_type= 'Pay to Till',
                                        trans_status= 'Pending',
                                        signatory_status='Pending',
                                        amount= amount,
                                        transaction_account_no=account,
                                        request_ref_id= 'Pending',
                                        name= name,
                                        narrative=narrative,
                                        org_id=existing_org.id,
                                        campaign_name= current_campaign.campaignName
                                    )  
        db.session.add(new_transaction)
        db.session.commit()
        

        # send mail to signatory
        for signatory in signatories:
            user = User.query.filter_by(id=signatory.user_id).first() 
            new_approval = TransactionApproval(transaction_id=new_transaction.id, signatory_id=signatory.id)
            db.session.add(new_approval)
            db.session.commit()

            sendMail.send_approval_message(user.firstName,user.email,existing_org.orgName,amount,new_transaction.trans_type,account)

        return jsonify({"message": "Your transaction was created and is awaiting approval."}), 200
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

#----------------------------------Webhooks----------------------------------------
#Intasend web hook for getting changes in transaction  status on mpesa stk push
@app.route('/api/v1.0/intasend-webhook', methods = ['POST'])
def collection_webhook():
    try:
        payload = request.json
        # print(payload)
        
        invoice_id = payload.get('invoice_id')
        net_amount = payload.get('net_amount')
        api_ref= payload.get('api_ref')        
        state = payload.get('state')
        donated_amount= payload.get('value')
        currency= payload.get('currency')
        provider= payload.get('provider')
        account= payload.get('account')
        email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

        if api_ref== "API Request":
            donation = Donation.query.filter_by(invoice_id=invoice_id).first()
            donation.method= provider
            db.session.commit()

        else:
            donation = Donation.query.filter_by(api_ref=api_ref).first()
            if donation.invoice_id == None:
                donation.invoice_id = invoice_id
                donation.currency= currency
                donation.amount = donated_amount
                donation.method= provider
                db.session.commit()
        
        if not donation:
            return  jsonify({"error":"Donation record not found"}),404
        
        donating_user= None
        if donation.user_id:
            donating_user= User.query.filter_by(id=donation.user_id).first()

        donation_campaign= Campaign.query.filter_by(id=donation.campaign_id).first()
        if not donation_campaign:
            return jsonify({'error':'campaign not listed'})
        
        campaign_organisation= Organisation.query.filter_by(id=donation_campaign.org_id).first()
        if not campaign_organisation:
            return jsonify({'error':'Organisation not found'})
        
        if state == "COMPLETE":
            
            # Update the donation status in the database
            donation.status = "COMPLETE"
            db.session.commit()

            if not main_pocket:
                return jsonify({"error": "Main pocket not found"})
            #send to pocket 
            app_commission= round((float(net_amount) * 0.15),2)  
            amount=app_commission
            narrative= "Msaada"

            if app_commission < float(10):
                return jsonify({"message":"No commission for this donation"})

            approved_response = service.wallets.intra_transfer(donation_campaign.walletId, main_pocket, amount, narrative) #wallet to wallet
            
            if approved_response.get("errors"):
                error_message = approved_response.get("errors")[0].get("detail")
                return  make_response(jsonify({'error':error_message}))
            
            if donating_user:
                sendMail.send_mail_on_donation_completion(donation.amount, 
                                                        donation.donationDate, 
                                                        donating_user.firstName, 
                                                        donation_campaign.campaignName,
                                                        donating_user.email, 
                                                        campaign_organisation.orgName)
                
            elif re.match(email_regex, account):
                sendMail.send_mail_on_donation_completion(
                    donation.amount,
                    donation.donationDate,
                    donating_user.firstName if donating_user else 'Supporter',
                    donation_campaign.campaignName,
                    account,
                    campaign_organisation.orgName)              
                

            return jsonify({"message":approved_response})
                
            
        elif state == "PROCESSING":
            donation.status = "PROCESSING"
            db.session.commit()

        elif state== "FAILED":
            donation.status="FAILED"   
            db.session.commit()        
            if  donating_user:
                sendMail.send_mail_donation_not_successiful(donation.amount, 
                                                        donation.donationDate, 
                                                        donating_user.firstName, 
                                                        donation_campaign.campaignName, 
                                                        donating_user.email,
                                                        campaign_organisation.orgName)
            elif re.match(email_regex, account):
                sendMail.send_mail_donation_not_successiful(
                    donation.amount,
                    donation.donationDate,
                    donating_user.firstName if donating_user else 'Supporter',
                    donation_campaign.campaignName,
                    account,
                    campaign_organisation.orgName
                )
            db.session.delete(donation)
            
        
        print ('Webhook received successfully')
    
    except Exception as e:
        print(f"Collecting hook error occurred: {e}")

#Intersend web hook to listen to changes in send money ie. Withdraw and buy airtime
@app.route('/api/v1.0/send-money-webhook', methods = ['POST'])
def send_money_webhook():
    try:
        payload = request.json

        tracking_id = payload.get('tracking_id')
        batch_status = payload.get('status')
        trans_status= payload.get('transactions')[0].get('status')

        existing_transaction= Transactions.query.filter_by(tracking_id=tracking_id).first()
        if not existing_transaction:
            print  ("Transaction record not found")
        
        #Update the transaction status in the database
        existing_transaction.batch_status= batch_status
        existing_transaction.trans_status= trans_status
        db.session.commit()

        existing_org= Organisation.query.filter_by(id=existing_transaction.org_id)
        if not existing_org:
            print ("organisation not found")

        if batch_status== "Completed" and trans_status == "complete":
            sendMail.send_mail_on_send_money_success(existing_org.orgEmail,existing_transaction.amount, existing_transaction.trans_type, existing_org.orgName)
        elif trans_status == "Unsuccessful" or batch_status=="Failed Processing" or trans_status== "failed":
            sendMail.send_mail_on_send_money_failure(existing_org.orgEmail,existing_transaction.amount, existing_transaction.trans_type, existing_org.orgName)

        
        print ('Webhook received successfully')
    
    except Exception as e:
        print(f"Send money hook error occurred: {e}")
        
#Route to check intasend transaction status
@app.route("/api/v1.0/check_transaction_status", methods=["POST"])
@jwt_required()
def check_transaction_status():
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.get(current_user_id)
    if not existing_org:
        return jsonify({"error": "organisation not found"}), 404

    try:
        data = request.get_json()
        tracking = data.get('tracking_id')
        if not tracking:
            return jsonify({"error": "Tracking ID is required"}), 400
        # Check if the transaction exists in the database
        existing_transaction = Transactions.query.filter_by(tracking_id=tracking).first()
        if not existing_transaction:
            return jsonify({"error": "Transaction not found"}), 404
        # Check the transaction status using the Intersend API and update the database with the status
        status = service.transfer.status(existing_transaction.tracking_id)
        if status.get("errors"):
            error_message = status.get("errors")[0].get("detail")
            return jsonify({"error": error_message}), 400
        
        existing_transaction.trans_status = status.get('transactions')[0].get('status')
        existing_transaction.batch_status = status.get("status")
        db.session.commit()

        return jsonify({"status": status})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
#============================== Transactions route===========================================================
#Get all transactions
class GetTransactions(Resource):
    @jwt_required()
    def get(self):
        current_user_id = get_jwt_identity()
        existing_org = Organisation.query.get(current_user_id)
        if not existing_org:
            return jsonify({"error": "organisation not found"}), 404
        try:
            # Get all campaigns for the current organisation
            all_transactions = Transactions.query.filter_by(org_id=existing_org.id).all()
            if not all_transactions:
                return jsonify({"error": "No transactions found"}), 404
            
            response_dict= [transaction.serialize() for transaction in all_transactions]
            return jsonify({"message":response_dict})

        except Exception as e:
            error_message = str(e)
            print("Error in GetTransactions:", error_message)
            return jsonify({"error": error_message}), 500

# get pdf 
@app.route ("/api/v1.0/withdraw_pdf", methods=["GET"])
@jwt_required()
def withdraw_pdf():
    current_user = get_jwt_identity()
    existing_org = Organisation.query.filter_by(id=current_user).first()
    if not existing_org:
        return jsonify({"error": "organisation not found"}), 404
    try:
        # Get all transactions for the current organisation
        transactions = Transactions.query.filter_by(org_id=current_user).all()
        if not transactions:
            return jsonify({"error": "No transactions found"}), 404

        # Create a PDF in memory
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)

        pdf.setTitle("Msaada_Mashinani/transactions")
        pdf.setFont("Helvetica", 12)

        logo_url = "https://res.cloudinary.com/dml7sp2zm/image/upload/b_rgb:FFFFFF/v1718886990/msaadaLogo-transparent_wac7jg.png"
        response = requests.get(logo_url)
        if response.status_code == 200:
            # Create a temporary file to store the logo image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()
        else:
            return jsonify({"error": "Failed to download logo image"}), 500

        # Draw logo
        def draw_logo(pdf):
            logo_width = 2 * inch
            logo_height = 1 * inch
            pdf.drawImage(tmp_file.name, x=0.5 * inch, y=10.5 * inch, width=logo_width, height=logo_height)
            pdf.drawString(2.8 * inch, 11 * inch, f"Transactions for {existing_org.orgName}")

        # Add table headers
        draw_logo(pdf)
        y = 10 * inch
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(0.5 * inch, y, "No.")
        pdf.drawString(6.6 * inch, y, "TransactionType")
        pdf.drawString(1 * inch, y, "Date")
        pdf.drawString(5.6 * inch, y, "Status")
        pdf.drawString(4.8 * inch, y, "Amount")
        pdf.drawString(3   * inch, y, "Campaign Name")
        pdf.drawString(2 * inch, y, "AccountNo")

        transactions_per_page = 20
        transaction_count = 0

        # Add the transactions
        y -= 0.5 * inch
        for index, transaction in enumerate(transactions, start=1):
            if transaction_count >= transactions_per_page or y < 1 * inch:
                pdf.showPage()

                y = 10 * inch
                transaction_count=0
                draw_logo(pdf)
                pdf.setFont("Helvetica-Bold", 12)
                pdf.drawString(0.5 * inch, y, "No.")
                pdf.drawString(6.6 * inch, y, "TransactionType")
                pdf.drawString(1 * inch, y, "Date")
                pdf.drawString(5.6 * inch, y, "Status")
                pdf.drawString(4.8 * inch, y, "Amount")
                pdf.drawString(3 * inch, y, "Campaign Name")
                pdf.drawString(2 * inch, y, "AccountNo")

                y -= 0.5 * inch

                # fetch transactions details
                # transactions = Transactions.query.filter_by(org_id=current_user).all()
            name_length = len(transaction.campaign_name)
            width = 25  # Default width
            if name_length > 25:
                width == 25
            
            campaign_name = textwrap.wrap(transaction.campaign_name, width=width)

            y -= 0.5 * inch
            transaction_count += 1
            pdf.setFont("Helvetica", 10)
            pdf.drawString(0.5 * inch, y, str(index))
            pdf.drawString(6.6 * inch, y, str(transaction.trans_type))
            pdf.drawString(1 * inch, y, transaction.transaction_date.strftime('%Y-%m-%d'))
            pdf.drawString(5.6 * inch, y, transaction.trans_status)
            pdf.drawString(4.8 * inch, y, str(transaction.amount))
            pdf.drawString(3   * inch, y, campaign_name[0])
            pdf.drawString(2 * inch, y, transaction.transaction_account_no)

            y -= 0.5 * inch
            transaction_count += 1

        total_pages = pdf.getPageNumber()

        # add a footer
        pdf.setFont("Helvetica", 10)
        pdf.drawString(1 * inch, 0.5 * inch, f"Page {pdf.getPageNumber()} of {total_pages}")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(1 * inch, 0.25 * inch, "Generated by @Msaada_Mashinani")
                        
        # You need to generate the PDF before returning it
        pdf.save()
        buffer.seek(0)
        
        return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": "attachment;filename=transactions.pdf"})

    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


    
#===============================Donation routes==============================================================
    
#Express donations route for user who is not logged in
class  ExpressDonations(Resource):
    def post(self):
        data= request.get_json()
        donor_name= data.get("donorName")
        email= data.get("donorEmail")
        phoneNumber= data.get("phoneNumber")
        amount= data.get('amount')
        campaign_id= data.get('campaignId')
        
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
            new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, donor_name=donor_name, status= data.get('invoice').get('state'), api_ref=data.get('invoice').get('api_ref') ,invoice_id= data.get('invoice').get('invoice_id'), method= "M-PESA")
            # print(new_donation)
            db.session.add(new_donation)
            db.session.commit()
            # return make_response(jsonify({"message": "Donation initialised successfully!", "data": new_donation.serialize()}), 200)
            return make_response(jsonify({"message": "Donation initialised successfully!", "data":data}), 200)
            # else:
            #     return make_response(jsonify({'error':'Error making donation'}), 400)
        except TypeError as ex:
            print(ex)
        except ValueError:
            return make_response(jsonify({"error": "Invalid value"}),400)  
        except Exception as e:
            print (e)
            if e:
                return make_response(jsonify({"error": f"Unexpected Error: {str(e)}"}), 400)

#Route to get all donations by a logged in organisation
@app.route("/api/v1.0/org_donations",methods=["GET"])
@jwt_required()
def get():
    current_user = get_jwt_identity()
    existing_org = Organisation.query.filter_by(id=current_user).first()
    if not existing_org:
        return {"error": "Organisation not found"}, 404
    try:
        all_campaigns= Campaign.query.filter_by(org_id=existing_org.id).all()
        all_campaign_id=[campaign.id for campaign in all_campaigns]
        all_donations=Donation.query.filter(Donation.campaign_id.in_(all_campaign_id)).all()
        if not all_donations:
            return {"error": "No donations found"}, 404
        response_dict = [donation.serialize() for donation in all_donations if donation.status=='COMPLETE' or donation.status=='PENDING']
        response = make_response(jsonify({"message":response_dict}),200)
        return response
    except  Exception as e:
        return make_response(jsonify({"error":"Internal Server Error:"+ str(e)}),500)

#Handle donation for logged users
class Donate(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return {"error": "User not found"}, 404
        all_donations = Donation.query.filter_by(user_id=user.id, status='COMPLETE').all()
        if not all_donations:
            return {"error": "No donations found"}, 404
        response_dict = [donation.serialize() for donation in all_donations]
        response = make_response(jsonify(response_dict),200)
        return response
       

    @jwt_required()
    def post(self):
        current_user= get_jwt_identity()
        user = User.query.filter_by(id=current_user).first()
        if not user:
            return {"error": "User not found"}, 404
        data= request.get_json()
        amount= data.get('amount')
        campaign_id= data.get('campaignId')
        phoneNumber = data.get('phoneNumber')
        donor_name= data.get('donorName')

        if not amount:
            return make_response(jsonify({"error":"Amount is required."}),400)
        if int(amount) <5:
                return make_response(jsonify({"error":"Donation must be above Kshs 5."}),400)

        try:
            existing_campaign= Campaign.query.get(campaign_id)
            if not existing_campaign:
                return {"error":"Campaign does not exist"},404

            response = service.wallets.fund(wallet_id=existing_campaign.walletId, email=user.email, phone_number=phoneNumber,
                                            amount=amount, currency="KES", narrative="Deposit", 
                                            mode="MPESA-STK-PUSH")
            # new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, user_id=user.id)
            data = response
            if data.get("errors"):
                error_message = data.get("errors")[0].get("detail")
                return  make_response(jsonify({"message":error_message}))
            # return jsonify(data)
            try:
                new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, user_id=user.id,donor_name=donor_name, status= data.get('invoice').get('state'), api_ref=data.get('invoice').get('api_ref'), invoice_id= data.get('invoice').get('invoice_id'), method= "M-PESA")
                # print(new_donation)
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

##Route to get all donations without authentication
@app.route('/api/v1.0/all_donations', methods=['GET'])
def get_all_donations():
    """Get a list of all Donations"""
    # all_donations= Donation.query.all()
    all_donations= Donation.query.filter_by(status='COMPLETE').all()
    donation_dict= [don.serialize() for don in all_donations]
    return {'message':donation_dict}

#=======================Donate via card/bitcoin/cashapp=============================================================
#---------------------Donate card when user is not logged in----------------------------------------------------------
@app.route('/api/v1.0/donate_card', methods=['POST'])
def donate_via_card():
    data= request.get_json()
    # donor_name= data.get("donorName")
    first_name= data.get('firstName')
    last_name= data.get('lastName')    
    email= data.get('cardEmail')
    phoneNumber= data.get("phoneNumber")
    currency= data.get('currency')
    amount= data.get('amount')
    campaign_id= data.get('campaignId')
    url = "https://sandbox.intasend.com/api/v1/checkout/"
    donor_names= ''

    if not amount:
        return make_response(jsonify({"error":"Amount is required."}), 400)
    if currency == "KES" and int(amount) <100:
            return make_response(jsonify({"error":"Donation must be above Kshs 100."}), 400)
    if int(amount) <1:
        return make_response(jsonify({"error":"Donation amount must be valid."}), 400)
    if not currency:
        return make_response(jsonify({"error":"Currency is required."}), 400)
    if first_name and last_name:
        donor_names= first_name + " " + last_name
    elif first_name:
        donor_names= first_name
    elif last_name:
        donor_names= last_name    
    else:
        donor_names= "Anonymous"
    
    res = ''.join(random.choices(string.ascii_uppercase+
                             string.digits, k=7)) #random value

    try:
        existing_campaign= Campaign.query.get(campaign_id)
        if not existing_campaign:
            return {"error":"Campaign does not exist"},404
        
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phoneNumber,
            "email": email,
            "wallet_id": existing_campaign.walletId,
            "method": "CARD-PAYMENT",
            "amount": amount,
            "redirect_url": "http://localhost:3000/thank-you",
            "currency": currency,
            "card_tarrif": "BUSINESS-PAYS",
            "api_ref": res
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-IntaSend-Public-API-Key": publishable_key
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.json().get('errors'):
            error_message = data.get('errors')[0].get('detail')
            # print(error_message)
            return  make_response(jsonify({'error':error_message}),400)
        
        new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id,donor_name= donor_names, api_ref=res, method= "CARD", currency= currency)
        db.session.add(new_donation)
        db.session.commit()

        return jsonify(response.json())
    
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while processing your request"}),400

#--------------------Donate card when user is logged in--------------------------------------------
@app.route('/api/v1.0/logged_in_donate_card', methods=['POST'])
@jwt_required()
def donate_via_card_logged_in():
    current_user_id = get_jwt_identity()
    existing_user= User.query.get(current_user_id)
    if not existing_user:
        return  jsonify({"error":"User does not exist"}),401

    data= request.get_json()
    currency= data.get('currency')
    amount= data.get('amount')
    campaign_id= data.get('campaignId')
    url = "https://sandbox.intasend.com/api/v1/checkout/"

    if not amount:
        return make_response(jsonify({"error":"Amount is required."}), 400)
    if currency == "KES" and int(amount) <100:
        return make_response(jsonify({"error":"Donation must be above Kshs 100."}), 400)
    if int(amount) <1:
        return make_response(jsonify({"error":"Donation amount must be valid."}), 400)
    if not currency:
        return make_response(jsonify({"error":"Currency is required."}), 400)
    
    res = ''.join(random.choices(string.ascii_uppercase+
                             string.digits, k=7)) #random value
    try:
        existing_campaign= Campaign.query.get(campaign_id)
        if not existing_campaign:
            return {"error":"Campaign does not exist"},404
        
        payload = {
            "first_name": existing_user.firstName,
            "last_name": existing_user.lastName,
            "phone_number": existing_user.phoneNumber,
            "email": existing_user.email,
            "wallet_id": existing_campaign.walletId,
            "method": "CARD-PAYMENT",
            "amount": amount,
            "redirect_url": "http://localhost:3000/thank-you",
            "currency": currency,
            "card_tarrif": "BUSINESS-PAYS",
            "api_ref": res
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "X-IntaSend-Public-API-Key": publishable_key
        }

        response = requests.post(url, json=payload, headers=headers)

        if response.json().get('errors'):
            error_message = data.get('errors')[0].get('detail')
            # print(error_message)
            return  make_response(jsonify({'error':error_message}),400)
        
        new_donation=Donation(amount= float(amount),campaign_id=existing_campaign.id, user_id=existing_user.id,donor_name= f"{existing_user.firstName} {existing_user.lastName}", api_ref=res, method= "CARD", currency= currency)
        # print(new_donation)
        db.session.add(new_donation)
        db.session.commit()

        return jsonify(response.json())
    
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred while processing your request"}),400

#=======================================Intasend routes==============================================================
# Get campaign transactions filters
@app.route('/api/v1.0/filter_transactions/<string:wallet_id>', methods=['POST','GET'])
@jwt_required()  
def wallet_transactions_filters(wallet_id):
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.get(current_user_id)
    if not existing_org:
        return  jsonify({"error":"Organisation does not exist"}),401
    
    if request.method== 'GET':
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

    if request.method == 'POST':
        data= request.get_json()
        trans_type= data.get('trans_type')
        start_date=data.get('start_date')
        end_date=data.get('end_date')

        # existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
        # if not existing_campaign:
        #     return  jsonify({"error":"Campaign does not exist'"}),404
        # wallet_id= existing_campaign.walletId
        # if wallet_id:
        url=f"https://sandbox.intasend.com/api/v1/transactions/?wallet_id={wallet_id}"
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
        
#===============================Transaction pdf route==============================================================
@app.route("/api/v1.0/transactions_pdf/<string:wallet_id>", methods=["GET"])
@jwt_required()
def get_transactions_pdf(wallet_id):
    current_user = get_jwt_identity()
    existing_org = Organisation.query.filter_by(id=current_user).first()
    if not existing_org:
        return jsonify({"error": "Organisation not found"}), 404
    
    wallet_id = request.args.get('wallet_id')  # Assuming wallet_id is passed as a query parameter

    url = f"https://sandbox.intasend.com/api/v1/transactions/?wallet_id={wallet_id}"
    try:
        headers = {
            "accept": "application/json",
            "Authorization": "Bearer " + token
        }
        response = requests.get(url, headers=headers)
        data = response.json()
        if data.get("errors"):
            error_message = data.get("errors")
            return make_response(jsonify({"error": error_message}), 400)
        
        # Create a PDF in memory
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        
        # Set PDF title and other metadata
        pdf.setTitle("Msaada_Mashinani/Transactions")
   
        # Load and add the logo
        logo_url = "https://res.cloudinary.com/dml7sp2zm/image/upload/v1718797966/msaadaLogo_syqygm.png"
         # Download the logo image from the URL
        response = requests.get(logo_url)
        
        if response.status_code == 200:
            # Create a temporary file to store the logo image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()  # Ensure data is written to the file
                
        else:
            return jsonify({"error": "Failed to download logo image"}), 500
        
        # draw logo
        def draw_logo(pdf):
            logo_width = 1 * inch
            logo_height = 1 * inch
            pdf.drawImage(tmp_file.name, x=0.5 * inch, y=10.5 * inch, width=logo_width, height=logo_height)
            pdf.drawString(1.8 * inch, 11 * inch, f"Transactions for {existing_org.orgName}")

    
        # Add table headers
        draw_logo(pdf)
        y = 10 * inch
        pdf.drawString(0.5 * inch, y, "No.")
        pdf.drawString(1 * inch, y, "TRANSACTION TYPE")
        pdf.drawString(3 * inch, y, "INVOICE ACC")
        pdf.drawString(5 * inch, y, "AMOUNT")
        pdf.drawString(6.5 * inch, y, "STATUS")

        # Iterate over transactions and add them to the PDF
        transactions = data.get("results")
        if transactions:
            y -= 0.5 * inch  # Move down a bit for the first row of data
            for index, transaction in enumerate(transactions, start=1):
                pdf.drawString(0.5 * inch, y, str(index))
                pdf.drawString(1 * inch, y, transaction.get("trans_type", ""))
                pdf.drawString(3 * inch, y, transaction.get("invoice", {}).get("account", ""))
                pdf.drawString(5 * inch, y, str(transaction.get("value", "")))
                pdf.drawString(6.5 * inch, y, transaction.get("status", ""))
                y -= 0.3 * inch  # Move down for the next row
        else:
            pdf.drawString(1 * inch, y - 0.3 * inch, "No transactions found")  # Display a message if no transactions found
                
        # You need to generate the PDF before returning it
        pdf.save()
        buffer.seek(0)
        
        return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": "attachment;filename=transactions.pdf"})

    
    except Exception as e:
        return jsonify({"error": "An error occurred while processing your request"}),500

#===============================Donation pdf route==============================================================

@app.route("/api/v1.0/org_donations_pdf", methods=["GET"])
@jwt_required()
def get_org_donations_pdf():
    current_user = get_jwt_identity()
    existing_org = Organisation.query.filter_by(id=current_user).first()
    if not existing_org:
        return jsonify({"error": "Organisation not found"}), 404
    
    try:
        # Get all donations for the organization
        all_campaigns = Campaign.query.filter_by(org_id=existing_org.id).all()
        all_campaign_id = [campaign.id for campaign in all_campaigns]
        all_donations = Donation.query.filter(Donation.campaign_id.in_(all_campaign_id)).all()
        
        if not all_donations:
            return jsonify({"error": "No donations found"}), 404
        
        # Create a PDF in memory
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=A4)
        
        # Set PDF title and other metadata
        pdf.setTitle("Msaada_Mashinani/Donation")
        
        # Add a title
        pdf.setFont("Helvetica-Bold", 12)
        # pdf.drawString(1.8 * inch, 11 * inch, f"Donations for {existing_org.orgName}")

         # Load and add the logo
        logo_url = "https://res.cloudinary.com/dml7sp2zm/image/upload/b_rgb:FFFFFF/v1718886990/msaadaLogo-transparent_wac7jg.png"
        
        # Download the logo image from the URL
        response = requests.get(logo_url)
        
        if response.status_code == 200:
            # Create a temporary file to store the logo image
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.flush()  # Ensure data is written to the file
                
        else:
            return jsonify({"error": "Failed to download logo image"}), 500
        
        # draw logo
        def draw_logo(pdf):
            logo_width = 2 * inch
            logo_height = 0.9 * inch
            pdf.drawImage(tmp_file.name, x=0.5 * inch, y=10.5 * inch, width=logo_width, height=logo_height)
            pdf.drawString(2.8 * inch, 11 * inch, f"Donations for {existing_org.orgName}")

    
        # Add table headers
        draw_logo(pdf)
        y = 10 * inch
        pdf.drawString(0.5 * inch, y, "No.")
        pdf.drawString(1 * inch, y, "Campaign")
        pdf.drawString(3 * inch, y, "Amount")
        pdf.drawString(5 * inch, y, "Invoice ID")
        pdf.drawString(6.5 * inch, y, "Status")
        
        # Initialize counter for number of donations per page
        donations_per_page = 21
        donation_count = 0

        pdf.setFont("Helvetica", 12)

        # Add the donations
        y -= 0.5 * inch
        for index, donation in enumerate(all_donations, start=1):
            if donation_count >= donations_per_page or y < 1 * inch:
                # Add a new page and reset the y-coordinate and counter
                pdf.showPage()

                y = 10 * inch
                donation_count = 0
                draw_logo(pdf)
                pdf.setFont("Helvetica-Bold", 12)
                # Redraw table headers on the new page
                pdf.drawString(0.5 * inch, y, "No.")
                pdf.drawString(1 * inch, y, "Campaign")
                pdf.drawString(3 * inch, y, "Amount")
                pdf.drawString(5 * inch, y, "Invoice ID")
                pdf.drawString(6.5 * inch, y, "Status")
                y -= 0.5 * inch
            
            # Fetch campaign details for each donation
            campaign = Campaign.query.filter_by(id=donation.campaign_id).first()

            # Determine the width based on the length of the campaign name
            name_length = len(campaign.campaignName)
            width = 25  # Default width
            if name_length > 25:
                width == 25

            campaign_name = textwrap.wrap(campaign.campaignName, width=width)
            print("Wrapped campaign name:",campaign_name)


            pdf.setFont("Helvetica", 12)
            # Add donation details to the PDF
            pdf.drawString(0.5 * inch, y, str(index))
            pdf.drawString(1 * inch, y, campaign_name[0])  # Limit campaign name length
            pdf.drawString(3 * inch, y, f"KSH {donation.amount:.2f}")
            pdf.drawString(5 * inch, y, donation.invoice_id)
            pdf.drawString(6.5 * inch, y, donation.status)
            
            # Move y-coordinate down and increment donation counter
            y -= 0.5 * inch
            donation_count += 1

        total_pages = pdf.getPageNumber()

        # Add a page footer
        pdf.setFont("Helvetica", 10)
        pdf.drawString(1 * inch, 0.5 * inch, f"Page {pdf.getPageNumber()} of {total_pages}")
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(1 * inch, 0.25 * inch, "Generated by @Msaada_Mashinani")
        
        # Finalize the PDF
        pdf.save()
        
        # Move the buffer position to the beginning
        buffer.seek(0)
        
        # Return the PDF file in the response
        return Response(buffer.getvalue(), mimetype="application/pdf", headers={"Content-Disposition": "attachment;filename=donations.pdf"})
    
    except Exception as e:
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500

#===============================Contact us form route==============================================================

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

#===============================Reset password routes==============================================================

# User forgot password reset
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

#Forgot account pin
@app.route('/api/v1.0/acc_forgot_pin', methods=['POST'])
def acc_forgot_pin():
    orgEmail = request.json.get('email')
    organisation = Organisation.query.filter_by(orgEmail=orgEmail).first()
    if organisation is None:
        return jsonify({"error": "No account associated with this email found!"}), 404
    else:
        otp = OTPGenerator.generate_otp()
        app.config['OTP_STORAGE'][orgEmail] = otp
        OTPGenerator.send_pin_otp(orgEmail, otp)
        return jsonify({'message': 'OTP sent to your email'}), 200
#Update pin
@app.route('/api/v1.0/acc_reset_pin', methods=['PATCH'])
def acc_reset_pin():
    orgEmail = request.json.get('email')
    otp_entered = request.json.get('otp')
    new_pin = request.json.get('new_pin')

    organisation = Organisation.query.filter_by(orgEmail=orgEmail).first()

    if organisation and orgEmail in app.config['OTP_STORAGE'] and app.config['OTP_STORAGE'][orgEmail] == otp_entered:
        account = Account.query.filter_by(orgId=organisation.id).first()
        if not account:
            return jsonify({'error': 'No account associated with this organization'}), 404
        
        try:
            account.pin = new_pin
            db.session.commit()
            return jsonify({'message': 'PIN reset successfully'}), 200
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    else:
        return jsonify({'error': 'Invalid OTP or email'}), 400



api.add_resource(userData, '/api/v1.0/users')
api.add_resource(userDataByid, '/api/v1.0/usersdata')
api.add_resource(campaignData, '/api/v1.0/campaigns')
api.add_resource(campaignById, '/api/v1.0/org_campaigns')
api.add_resource(OrgCampaigns, '/api/v1.0/org_all_campaigns')    
api.add_resource(addAccount, '/api/v1.0/accounts')
api.add_resource(accountById , '/api/v1.0/orgaccounts/<int:id>')
api.add_resource(Organization, '/api/v1.0/organisations')
api.add_resource(OrganisationDetail, '/api/v1.0/organisation')
api.add_resource(Donate, '/api/v1.0/user/donations')
api.add_resource(ExpressDonations, '/api/v1.0/express/donations')
api.add_resource(GetTransactions, '/api/v1.0/withdraw_transactions')
api.add_resource(GetSubscription, '/api/v1.0/subscription/<int:org_id>')
api.add_resource(OrgSubscriptions, '/api/v1.0/org_subscription')
api.add_resource(Signatories, '/api/v1.0/signatories')
api.add_resource(SignatoryDetail, '/api/v1.0/signatories/<int:id>')


if __name__  =="__main__":
    app.run (port =5555, debug =True)