#Flask app
from flask import Flask, request,jsonify,make_response
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation
import os
from dotenv import load_dotenv
import random
load_dotenv()
from intasend import APIService
import uuid
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt

#fetch environment variables  for the api key and server url
token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
service = APIService(token=token,publishable_key=publishable_key, test=True)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///msaada.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)
bcrypt = Bcrypt(app)


# classes for users
class userData (Resource):
    def get(self):
        users = [user.serialize() for user in User.query.filter_by(isActive = True).all()]
        response = make_response(jsonify(users))
        return response
    
    def post(self):
        data = request.get_json()
        firstName = data['firstName']
        lastName = data['lastName']
        username = data['username']
        email = data['email']
        nationalId = data['nationalId']
        phoneNumber = data['phoneNumber']
        address = data['address']
        hashed_password  = data['password']
        isActive = db.Column(db.Boolean, default=True)  # New field

        existing_username =  User.query.filter_by(username=username).first()
        if existing_username:
            return {"Error":"Username already exists"}, 400
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return {"Error":"Email already exists"}, 400
        exiting_nationalId = User.query.filter_by(nationalId=nationalId).first()
        if exiting_nationalId:
            return {"Error":"National ID already exists"}, 400
        existing_phoneNumber = User.query.filter_by(phoneNumber=phoneNumber).first()
        if existing_phoneNumber:
            return {"Error":"Phone number already exists"}, 400
        
       
        
        new_user = User(firstName=firstName, 
                        lastName=lastName, 
                        username=username, 
                        email=email, 
                        nationalId=nationalId,
                        phoneNumber=phoneNumber, 
                        address=address, 
                        password=hashed_password,
                        isActive=isActive
                          )
      
        db.session.add(new_user)
        db.session.commit()

        response = make_response(jsonify(new_user.serialize()),200)
        return response

api.add_resource(userData, '/users')

    
class userDataByid(Resource):
    def get(self,id):
        user = User.query.get(id)
        if not user:
            return {"Error":"User not found"}, 404
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
            return {"Error": "User not found"}, 404

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
            user.isActive = False       
            # db.session.delete(user)
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
            return jsonify({"Error":"Please provide complete information"}),400
        
        available_org= Organisation.query.filter_by(id=org_id).first()
        if not available_org:
            return jsonify({"Error":"Organisation does not exist."}),404

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
            return jsonify({"Error":"Error creating wallet"}),400
        
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
            return {"Error":"Campaign not found"}, 404
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
            return jsonify({ "Error":"Campaign not found"}), 404
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

class Organization(Resource):
    def get(self):
        organizations = Organisation.query.all()
        serialized_organizations = [org.serialize() for org in organizations]
        return (serialized_organizations), 200
    
    def post(self):
        data = request.get_json()
        orgName = data['orgName']
        orgEmail = data['orgEmail']
        orgPassword = data['password']
        orgAddress = data['orgAddress']
        orgPhoneNumber = data['orgPhoneNumber']
        orgDescription = data['orgDescription']

        existing_orgName = Organisation.query.filter_by(orgName=orgName).first()
        if existing_orgName:
            return {"Message": "An organisation with this name already exists."},400
        
        existing_orgEmail =  Organisation.query.filter_by(orgEmail=orgEmail).first()
        if existing_orgEmail:
            return{"Message":"This email is already registered to an organization"},400
        
        existing_orgPhoneNumber =  Organisation.query.filter_by(orgPhoneNumber=orgPhoneNumber).first()
        if existing_orgPhoneNumber:
            return{"Message":"This Phone number is already registered to an organization"}, 400
        
        new_organisation =  Organisation(orgName=orgName, orgEmail=orgEmail, password=orgPassword,orgPhoneNumber=orgPhoneNumber, orgAddress=orgAddress, orgDescription=orgDescription)
        db.session.add(new_organisation)
        db.session.commit()

        response = make_response(jsonify(new_organisation.serialize(),200))
        return response

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


if __name__  =="__main__":
    app.run (port =5555, debug =True)