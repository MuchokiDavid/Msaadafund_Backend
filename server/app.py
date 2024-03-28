#Flask app
from flask import Flask, request,jsonify,make_response
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation,Account,TokenBlocklist
from utility import check_wallet_balance
import os
from dotenv import load_dotenv
load_dotenv()
from intasend import APIService
import uuid
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager,jwt_required,get_jwt_identity
from auth import auth_bp

#fetch environment variables  for the api key and server url
token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
service = APIService(token=token,publishable_key=publishable_key, test=True)

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = b'\xb2\xd3B\xb9 \xab\xc0By\x13\x10\x84\xb7M!\x11'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 60 * 60
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///msaada.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager()
jwt.init_app(app)


# register blueprint
app.register_blueprint(auth_bp, url_prefix='/auth')

# jwt error handler
@jwt.expired_token_loader
def expired_token(jwt_header,jwt_data):
    return jsonify({'message': 'The token has expired.','error':'token expired'}), 401

@jwt.invalid_token_loader
def invalid_token(error):
    return jsonify({'message': 'Does not contain a valid token.','error':'invalid token'}), 401

@jwt.unauthorized_loader
def missing_token(error):
    return jsonify({'message': 'Request does not contain an access token.', 'error':'token missing'}), 401


@jwt.token_in_blocklist_loader #check if the jwt is revocked
def token_in_blocklist(jwt_header,jwt_data):
    jti = jwt_data['jti']

    token = db.session.query(TokenBlocklist).filter(TokenBlocklist.jti == jti).scalar()
# if token is none : it will return false 
    return token is not None


# classes for users
class userData (Resource):
    def get(self):
        users = [user.serialize() for user in User.query.filter_by(isActive = True).all()]
        response = make_response(jsonify(users))
        return response
    
   
api.add_resource(userData, '/users')

    
class userDataByid(Resource):
    def get(self,id):
        user = User.query.get(id)
        if not user:
            return {"error":"User not found"}, 404
        response = make_response(jsonify(user.serialize()))
        return response
    
    def patch(self, id):
        data = request.get_json()
        firstName = data.get('firstName')
        lastName = data.get('lastName')
        phoneNumber = data.get('phoneNumber')
        address = data.get('address')

        existing_user = User.query.get(id)
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

        response = make_response(jsonify(existing_user.serialize()))
        return response
  

    def delete(self,id):
        user = User.query.get(id)
        if not user:
            return "User not found", 404
        else:
            # user.isActive = False       
            db.session.delete(user)
            db.session.commit()

            return {"message": "User deleted successfully"},200   
    
api.add_resource(userDataByid, '/users/<int:id>')

#get campaigns
class campaignData(Resource):
    # @jwt_required()
    def get(self):
        all_campaigns = [campaign.to_dict() for campaign in Campaign.query.filter_by(isActive=True).all()]
        response = make_response(jsonify(all_campaigns), 200)
        return response
    
    # @jwt_required()
    def post(self):
        data=request.get_json()
        campaignName = data.get('name')
        description = data.get('description')
        category= data.get('category')
        banner= data.get('banner')
        startDate = data.get('startDate')
        endDate = data.get('endDate')
        targetAmount = float(data.get('targetAmount'))
        isActive= data.get('isActive') 
        org_id= data.get('orgId')

        if not (campaignName and description and startDate and endDate):
            return jsonify({"error":"Please provide complete information"}),400
        
        available_org= Organisation.query.filter_by(id=org_id).first()
        if not available_org:
            return jsonify({"error":"Organisation does not exist."}),404

        new_campaign = Campaign(campaignName= campaignName, 
                                description= description, 
                                category= category,
                                banner= banner,
                                startDate=startDate, 
                                endDate= endDate, 
                                targetAmount=targetAmount, 
                                isActive= bool(isActive), # bool("") => False
                                org_id= org_id
                                )
            
        #create wallet
        intasend_response = service.wallets.create(currency="KES", label=f"Camp{uuid.uuid4()}", can_disburse=True)

        if intasend_response.get('errors'):
            return jsonify({"error":"error creating wallet"}),400
        
        #add wallet id to instance
        new_campaign.walletId=intasend_response.get("wallet_id")
        db.session.add(new_campaign)
        db.session.commit()
        return make_response(jsonify({"success": "Campaign created successfully!", "data": new_campaign.to_dict()}), 201)


api.add_resource(campaignData, '/campaigns')

#Get inactive campaigns
@app.route('/getinactive', methods=['GET'])
def  getInactiveCampaign():
    """Return a list of all inactive campaigns"""
    all_campaigns = [campaign.to_dict() for campaign in Campaign.query.filter_by(isActive=False).all()]
    response = make_response(jsonify(all_campaigns), 200)
    return response
    

#Get  specific campaign details by id
class campaignById(Resource):
    # @jwt_required
    def get(self,id):
        campaign = Campaign.query.get(id)
        if not campaign:
            return {"error":"Campaign not found"}, 404
        response = make_response(jsonify(campaign.to_dict()))
        return response

    # @jwt_required
    def patch (self,id):
        data=request.get_json()
        description = data.get('description')
        endDate = data.get('endDate')
        targetAmount = data.get('targetAmount')
        isActive= data.get('isActive')

        existing_campaign = Campaign.query.filter(id==id).first()

        if not existing_campaign:
            return jsonify({ "error":"Campaign not found"}), 404
        if description:
            existing_campaign.description = description
        if endDate:
            existing_campaign.endDate =endDate
        if targetAmount:
            existing_campaign.targetAmount = targetAmount
        if isActive:
            isActive = True if isActive.lower() == 'true' else False
            existing_campaign.isActive = isActive

        db.session.commit()
        
        response = make_response(jsonify(existing_campaign.to_dict()))
        return response
    

    def delete(self,id):
        campaign = Campaign.query.get(id)
        if not campaign:
            return "Campaign not found", 404
        else:
            campaign.isActive = False       
            # db.session.delete(campaign)
            db.session.commit()

            return {"message": "Campaign deactivated successfully"},200   

api.add_resource(campaignById, '/campaigns/<int:id>')

#Get wallet balance for a campaign
@app.route('/campaign_wallet/<int:id>', methods=['GET'])
# @jwt_required()
def check_wallet(id):
    # current_user_id = get_jwt_identity()
    # existing_campaign= Campaign.query.filter_by(id=id).first()
    existing_campaign= Campaign.query.get(id)
    if not existing_campaign:
        return jsonify({ "error":"Campaign not found"}), 404
    wallet_id= existing_campaign.walletId
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

    def post(self):
        data= request.get_json()
        accountType= data.get('accountType')
        accountNumber= data.get('accountNumber')
        orgId= data.get('orgId')
        try:
            new_account= Account(accountType=accountType, accountNumber=accountNumber, orgId=orgId )
            db.session.add(new_account)
            db.session.commit()
            return {"Message": "New account added successfully"}, 201
        except Exception  as e:
             return {"error": "Account already registered"},500  


api.add_resource(addAccount, '/accounts')

#Get account by id
class accountById(Resource):
    # @jwt_required()
    def get(self, id):
        account = Account.query.get(id)
        if not account:
            return {"error":"Account not found"}, 404
        response = make_response(jsonify(account.serialize()))
        return response
    
    def delete(self,id):
        account = Account.query.get(id)
        if not account:
            return "Account not found", 404
        else:     
            db.session.delete(account)
            db.session.commit()

            return {"message": "Account deleted successfully"},200   

api.add_resource(accountById , '/accounts/<int:id>')

class Organization(Resource):
    def get(self):
        organizations = Organisation.query.all()
        serialized_organizations = [org.serialize() for org in organizations]
        return (serialized_organizations), 200
    
    # def post(self):
    #     data = request.get_json()
    #     orgName = data['orgName']
    #     orgEmail = data['orgEmail']
    #     orgPassword = data['password']
    #     orgAddress = data['orgAddress']
    #     orgPhoneNumber = data['orgPhoneNumber']
    #     orgDescription = data['orgDescription']

    #     existing_orgName = Organisation.query.filter_by(orgName=orgName).first()
    #     if existing_orgName:
    #         return {"Message": "An organisation with this name already exists."},400
        
    #     existing_orgEmail =  Organisation.query.filter_by(orgEmail=orgEmail).first()
    #     if existing_orgEmail:
    #         return{"Message":"This email is already registered to an organization"},400
        
    #     existing_orgPhoneNumber =  Organisation.query.filter_by(orgPhoneNumber=orgPhoneNumber).first()
    #     if existing_orgPhoneNumber:
    #         return{"Message":"This Phone number is already registered to an organization"}, 400
        
    #     new_organisation =  Organisation(orgName=orgName, orgEmail=orgEmail, password=orgPassword,orgPhoneNumber=orgPhoneNumber, orgAddress=orgAddress, orgDescription=orgDescription)
    #     db.session.add(new_organisation)
    #     db.session.commit()

    #     response = make_response(jsonify(new_organisation.serialize(),200))
    #     return response

api.add_resource(Organization, '/organisations')


class OrganisationDetail(Resource):
    def get(self, id):
        org = Organisation.query.get(id)
        if not org :
            return {'message':'Organisation does not exist'}, 404
        return make_response(jsonify(org.serialize()))
    
    def delete(self, id):
        org = Organisation.query.get(id)
        if not org:
            return{'message': 'Organisation does not exist'} ,  404
        db.session.delete(org)
        db.session.commit()
        return {'message' : 'Organisation deleted successfully'}, 200
    
    def patch(self, id):
        data = request.get_json()
        orgName = data.get('orgName')
        orgEmail = data.get('orgEmail')
        orgPhoneNumber = data.get('orgPhoneNumber')
        orgAddress = data.get('orgAddress')
        orgDescription = data.get('orgDescription')

        existing_org = Organisation.query.filter_by(id=id).first()
        if not existing_org:
            return {"Message": "Organisation does not exist"}, 404
        
        if orgName:
            existing_org.orgName = orgName
        if orgEmail:
            existing_org.orgEmail = orgEmail
        if orgPhoneNumber:
            existing_org.orgPhoneNumber = orgPhoneNumber
        if orgAddress:
            existing_org.orgAddress = orgAddress
        if orgDescription:
            existing_org.orgDescription = orgDescription

        db.session.commit()
        return {"Message": "Organisation has been updated", "Data": existing_org.serialize()}
    

api.add_resource(OrganisationDetail, '/organisations/<int:id>')

#Route to withdraw money to M-pesa number
@app.route("/withdraw/mpesa",methods=["POST"])
# @jwt_required()
def mpesa_withdrawal():
    data=request.get_json()
    accountType= data.get("accountType")
    accountNumber= data.get("accountNumber")
    amount=float(data.get('amount'))
    orgId= int(data.get('orgId'))# use jwt_identity
    campaign=int(data.get("campaign"))

    account= Account.query.filter_by(accountType=accountType,accountNumber=accountNumber,orgId=orgId).first()
    if account is None:
        return jsonify({"error": "No such account"}),404
    
    organisation= Organisation.query.get(orgId)
    if not organisation:
        return jsonify({"error":"Invalid organization ID"}),401
    
    campaigns= Campaign.query.filter_by(id=campaign, org_id=orgId, isActive=True).first()
    if not campaigns:
        return jsonify({"error":"Campaign does not exist or inactive."}),404
    
    #check wallet balance
    if float(check_wallet_balance(campaigns.walletId))<float(amount):
        return jsonify({"error":"Insufficient funds in the wallet!"})
    try: 
        if accountType=="M-Pesa":
            transactions = [{'name': organisation.orgName, 'account': account.accountNumber, 'amount': int(amount)}]

            response = service.transfer.mpesa(wallet_id=campaigns.walletId, currency='KES', transactions=transactions)
            if response.get('errors'):
                error_message= response.get('errors')[0].get('detail')
                return jsonify({'Error':error_message})
            return jsonify(response)
        
        else:
            return jsonify({"error":"Please select M-pesa"}),404
    except Exception as e :
        return jsonify({"error":str(e)}),500

@app.route('/description', methods=["PUT"])
@jwt_required()
def update_org_description():
    current_organisation_id = get_jwt_identity()

    organization = Organisation.query.get(current_organisation_id)

    if not organization:
        return jsonify({'error': 'Organization not found'}), 404


    data = request.get_json()
    new_description = data.get('description')

    if not new_description:
        return jsonify({'error': 'New description is required'}), 400

    organization.orgDescription = new_description

    db.session.commit()

    return jsonify({"message": "Description updated successfully"}), 200


if __name__  =="__main__":
    app.run (port =5555, debug =True)