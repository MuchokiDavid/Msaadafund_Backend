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
import requests
from datetime import datetime
from flask_jwt_extended import JWTManager,jwt_required,get_jwt_identity
from auth import auth_bp
from flask_mail import Mail


#fetch environment variables  for the api key and server url
token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
service = APIService(token=token,publishable_key=publishable_key, test=True)

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = b'\xb2\xd3B\xb9 \xab\xc0By\x13\x10\x84\xb7M!\x11'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = 24 * 60 * 60
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///msaada.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'msaadamashinani@gmail.com'
app.config['MAIL_PASSWORD'] = 'yaadxnrowrgglbmt'
app.config['MAIL_DEFAULT_SENDER'] = 'msaadamashinani@gmail.com'


migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)
bcrypt = Bcrypt(app)
jwt = JWTManager()
jwt.init_app(app)
mail = Mail(app)

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

# @app.route('/usersdata', methods=['GET']) 
# @jwt_required()
# def get():
#     current_user = get_jwt_identity()
#     user = User.query.filter_by(username=current_user).first()
#     if not user:
#         return {"error":"User not found"}, 404
#     response = make_response(jsonify(user.serialize()),200)
#     return response   

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

        response = make_response(jsonify(existing_user.serialize()))
        return response
  
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        user = User.query.filter_by(username = current_user).first()
        if not user:
            return "User not found", 404
        else:
            user.isActive = False       
            # db.session.delete(user)
            db.session.commit()

            return {"message": "User deactivated successfully"},200   
    
api.add_resource(userDataByid, '/usersdata')

#get campaigns
class campaignData(Resource):
    # @jwt_required()
    def get(self):
        all_campaigns = [campaign.serialize() for campaign in Campaign.query.filter_by(isActive=True).all()]
        response = make_response(jsonify(all_campaigns), 200)
        return response

api.add_resource(campaignData, '/campaigns')

#Get inactive campaigns
@app.route('/getinactive', methods=['GET'])
def  getInactiveCampaign():
    """Return a list of all inactive campaigns"""
    all_campaigns = [campaign.to_dict() for campaign in Campaign.query.filter_by(isActive=False).all()]
    response = make_response(jsonify(all_campaigns), 200)
    return response

@app.route('/campaignpatch', methods=['PATCH'])
@jwt_required()
def patch ():
    current_user = get_jwt_identity()
    existing_organisation = Organisation.query.filter_by(id=current_user).first()

    if not existing_organisation:
        return {"error":"Organisation not found"}, 404
    data=request.get_json()
    description = data.get('description')
    endDate = data.get('endDate')
    targetAmount = data.get('targetAmount')
    isActive= data.get('isActive')

    existing_campaign = Campaign.query.filter_by(campaignName=data['name']).first()
    if not existing_campaign:
        return {"error":"Campaign not found"}, 404
    if description:
        existing_campaign.description = description
    if endDate:
        existing_campaign.endDate = endDate
    if targetAmount:
        existing_campaign.targetAmount = targetAmount
    if isActive:
        isActive = True if isActive.lower() == 'true' else False
        existing_campaign.isActive = isActive

    db.session.commit()
    
    response = make_response(jsonify(existing_campaign.serialize()))
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
       
    
    @jwt_required()
    def post(self):
        current_user = get_jwt_identity()
        data=request.get_json()
        campaignName = data.get('name')
        description = data.get('description')
        category= data.get('category')
        banner= data.get('banner')
        startDateStr = data.get('startDate')
        endDateStr = data.get('endDate')
        targetAmount = float(data.get('targetAmount'))
        # isActive= data.get('isActive') # issue 1 


       
        
        available_org= Organisation.query.filter_by(id=current_user).first()
        if not available_org:
            return jsonify({"error":"Organisation does not exist."}),404
        # print(available_org.orgName)

        # Convert date strings to Python date objects
        startDate = datetime.strptime(startDateStr, '%Y-%m-%d').date()
        endDate = datetime.strptime(endDateStr, '%Y-%m-%d').date()


        current_date = datetime.now().date()
        if startDate and endDate < current_date:
            return {'error': 'cannot create a campaign in the past'}, 400 
        if endDate < startDate:
            return {'error': 'end date cannot be before start date'}, 400
        

        if not (campaignName and description and startDate and endDate):
            return jsonify({"error":"Please provide complete information"}),400
        
        if startDate == current_date:
            isActive = True
        elif startDate > current_date:
            isActive = False
        elif endDate > current_date:
            isActive = False

             
        

        new_campaign = Campaign(campaignName= campaignName, 
                                description= description, 
                                category= category,
                                banner= banner,
                                startDate=startDate, 
                                endDate= endDate, 
                                targetAmount=targetAmount, 
                                isActive= bool(isActive), # bool("") => False
                                org_id=available_org.id
                                )
            
        #create wallet
        intasend_response = service.wallets.create(currency="KES", label=f"Camp{uuid.uuid4()}", can_disburse=True)

        if intasend_response.get('errors'):
            return jsonify({"error":"error creating wallet"}),400
        
        #add wallet id to instance
        new_campaign.walletId=intasend_response.get("wallet_id")
        db.session.add(new_campaign)
        db.session.commit()


        send_post_campaign(available_org, campaignName, description, category, targetAmount)

        return make_response(jsonify({"success": "Campaign created successfully!", "data": new_campaign.to_dict()}), 201)

def send_post_campaign(organisation, campaignName, description, category, targetAmount):
    subject = "Campaign Created Successfully"
    body = f"A new campaign has been created successfully.\n\n" \
           f"Campaign Name: {campaignName}\n" \
           f"Description: {description}\n" \
           f"Category: {category}.\n" \
           f"Your target amount is Ksh: {targetAmount}"

    mail.send_message(subject=subject, recipients=[organisation.orgEmail], body=body)


        return make_response(jsonify({"success": "Campaign created successfully!", "data": new_campaign.serialize()}), 201)
    
    @jwt_required()
    def delete(self):
        data=request.get_json()
        current_user = get_jwt_identity()
        organisation = Organisation.query.filter_by(id=current_user).first()
        
        if not organisation:
            return {"Organisation not found"}, 404
        
        existing_campaign = Campaign.query.filter_by(campaignName=data['name']).first()
        if not existing_campaign:
            return "Campaign not found", 404
        else:
            existing_campaign.isActive = False       
            # db.session.delete(campaign)
            db.session.commit()

            return {"message": "Campaign deactivated successfully"},200   

api.add_resource(campaignById, '/orgcampaigns')

#Get inactive campaigns
@app.route('/get_inactive_campaign', methods=['GET'])
def  getInactiveCampaign():
    """Return a list of all inactive campaigns"""
    all_campaigns = [campaign.to_dict() for campaign in Campaign.query.filter_by(isActive=False).all()]
    response = make_response(jsonify(all_campaigns), 200)
    return response

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
    
api.add_resource(addAccount, '/accounts')

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
        response = make_response(jsonify(data))
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
             return {"error": "Account already registered"},500  

    
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

api.add_resource(accountById , '/orgaccounts')

class Organization(Resource):
    def get(self):
        organizations = Organisation.query.all()
        serialized_organizations = [org.serialize() for org in organizations]
        return (serialized_organizations), 200

api.add_resource(Organization, '/organisations')


class OrganisationDetail(Resource):
    @jwt_required()
    def get(self):
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id=current_user).first()
        if not org :
            return {'message':'Organisation does not exist'}, 404
        return make_response(jsonify(org.serialize()))
   
    @jwt_required()
    def delete(self):
        current_user = get_jwt_identity()
        org = Organisation.query.filter_by(id = current_user)
        if not org:
            return{'message': 'Organisation does not exist'} ,  404
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
            return {"Message": "Organisation does not exist"}, 404
        
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
        return {"Message": "Organisation has been updated", "Data": existing_org.serialize()}
    

api.add_resource(OrganisationDetail, '/organisation')

#Route to get banks and their code in intersend API
@app.route('/all_banks', methods=['GET'])
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
@app.route("/withdraw",methods=["POST"])
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
        return jsonify({"error":"Insufficient funds in the wallet!"})
    try: 
        if accountType=="M-Pesa":
            #Initiate intasend M-Pesa transaction
            transactions = [{'name': organisation.orgName, 'account': account.accountNumber, 'amount': int(amount)}]

            response = service.transfer.mpesa(wallet_id=campaigns.walletId, currency='KES', transactions=transactions)
            if response.get('errors'):
                error_message= response.get('errors')[0].get('detail')
                return jsonify({'Error':error_message})
            return jsonify(response)
        
        elif accountType=="Bank":
            return jsonify({"message":"Bank transaction will be here"})
        else:
            return jsonify({"message":"Select transaction"})

        
    except Exception as e :
        print(e)
        return jsonify({"error":str(e)}),500


# @app.route('/description', methods=["PUT"])
# @jwt_required()
# def update_org_description():
#     current_organisation_id = get_jwt_identity()

#     organization = Organisation.query.get(current_organisation_id)

#     if not organization:
#         return jsonify({'error': 'Organization not found'}), 404


#     data = request.get_json()
#     new_description = data.get('description')

#     if not new_description:
#         return jsonify({'error': 'New description is required'}), 400

#     organization.orgDescription = new_description

#     db.session.commit()

#     return jsonify({"message": "Description updated successfully"}), 200

#route to handle donations
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
        # email= data.get('email') #use current user email issue 3
        # phoneNumber= data.get("phoneNumber")
        # email = user.email 
        # phoneNumber = user.phoneNumber
        amount= data.get('amount')
        campaign_id= data.get('campaignId')


        # if not email:
        #     return jsonify({"error":"Email is required."}),400
        
        # if not phoneNumber:
        #     return jsonify({"error":"Phone number is required."}),400

        if not amount:
            return jsonify({"error":"Amount is required."}),400
        
        if int(amount) <5:
            return jsonify({"error":"Donation must be above Kshs 5."}),400

        try:
            existing_campaign= Campaign.query.get(campaign_id)
            if not existing_campaign:
                return {"error":"Campaign does not exist"},404

            service = APIService(token=token,publishable_key=publishable_key, test=True)

            response = service.wallets.fund(wallet_id=existing_campaign.walletId, email=user.email, phone_number=user.phoneNumber,
                                            amount=amount, currency="KES", narrative="Deposit", 
                                            mode="MPESA-STK-PUSH")
            print (user.email)
            return jsonify(response)
        
        # new_donation=Donation(email,phoneNumber,float(amount),existing_campaign.id)
            
            # db.session.add(new_donation)
            # db.session.commit()
            # send_email(f'{new_donation.name()} has made a donation of ${new_donation.amount} to {new_donation.campaign().
            # send_express_donation_email(email,phoneNumber,amount,existing_campaign.name)
            # return jsonify(f'Thank you for your support! Your donation of ${amount} has been recorded and an email with further instructions
        except Exception as e:
            print (e)
            return jsonify({"error": "An error occurred while processing your request"}),500

api.add_resource(Donate, '/user/donations')

#Express donations route for user who is not logged in
@app.route('/express/donations', methods = ['POST'])
def express_donation():
    data= request.get_json()
    email= "anonymous@gmail.com"
    phoneNumber= data.get("phoneNumber")
    amount= data.get('amount')
    campaign_id= data.get('campaignId')

    if not email:
        return jsonify({"error":"Email is required."}),400
    
    if not phoneNumber:
        return jsonify({"error":"Phone number is required."}),400

    if not amount:
        return jsonify({"error":"Amount is required."}),400
    if int(amount) <5:
            return jsonify({"error":"Donation must be above Kshs 5."}),400

    try:
        existing_campaign= Campaign.query.filter_by(id=campaign_id).first()
        if not existing_campaign:
            return  jsonify({"error":"Campaign does not exist"}),404

        response = service.wallets.fund(wallet_id=existing_campaign.walletId, email=email, phone_number=phoneNumber,
                                        amount=amount, currency="KES", narrative="Deposit", 
                                        mode="MPESA-STK-PUSH")
        return jsonify(response)
    
     # new_donation=Donation(email,phoneNumber,float(amount),existing_campaign.id)
        
        # db.session.add(new_donation)
        # db.session.commit()
        # send_email(f'{new_donation.name()} has made a donation of ${new_donation.amount} to {new_donation.campaign().
        # send_express_donation_email(email,phoneNumber,amount,existing_campaign.name)
        # return jsonify(f'Thank you for your support! Your donation of ${amount} has been recorded and an email with further instructions
    except Exception as e:
        print (e)
        return jsonify({"error": "An error occurred while processing your request"}),500

#Get all campaign transactions
@app.route('/all_transactions/<int:id>', methods=['GET'])
@jwt_required()  
def wallet_transactions(id):
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.filter_by(id=current_user_id).first()
    if not existing_org:
        return  jsonify({"Error":"Organisation does not exist"}),401

    #checking a if a campaign exist
    existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
    if not existing_campaign:
        return  jsonify({"Error":"Campaign does not exist'"}),404
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
@app.route('/filter_transactions/<int:id>', methods=['POST'])
# @jwt_required()  
def wallet_transactions_filters(id):
    current_user_id = get_jwt_identity()
    existing_org= Organisation.query.get(current_user_id)
    if not existing_org:
        return  jsonify({"Error":"Organisation does not exist"}),401
    
    data= request.get_json()
    trans_type= data.get('trans_type')
    start_date=data.get('start_date')
    end_date=data.get('end_date')

    existing_campaign= Campaign.query.filter_by(org_id=existing_org.id,id=id).first()
    if not existing_campaign:
        return  jsonify({"Error":"Campaign does not exist'"}),404
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


if __name__  =="__main__":
    app.run (port =5555, debug =True)