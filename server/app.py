#Flask app
from flask import Flask
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt
from flask import request,jsonify,make_response

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
        users = [user.serialize() for user in User.query.all()]
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
        
       
        
        new_user = User(firstName=firstName, lastName=lastName, username=username, email=email, nationalId=nationalId, phoneNumber=phoneNumber, address=address, password=hashed_password)
      
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

    def patch (self,id):
        data = request.get_json()
        firstName = data['firstName']
        lastName = data['lastName']
        phoneNumber = data['phoneNumber']
        address = data['address']

        existing_user = User.query.get(id)
        if not existing_user:
            return{ "Error":"User not found"}, 404
        else:
            existing_user.firstName = firstName
            existing_user.lastName = lastName
            existing_user.phoneNumber = phoneNumber
            existing_user.address = address
            db.session.commit()
            
            response = make_response(jsonify(existing_user.serialize()))
            return response
    

    def delete(self,id):
        user = User.query.get(id)
        if not user:
            return "User not found", 404
        else:
            user.isActive = False       
            db.session.delete(user)
            db.session.commit()

            return {"message": "User deleted successfully"},200   
    
api.add_resource(userDataByid, '/users/<int:id>')


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