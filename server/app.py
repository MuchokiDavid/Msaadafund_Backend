#Flask app
from flask import Flask
from flask_migrate import Migrate
from flask_restful import Api,Resource
from models import db, User, Donation, Campaign, Organisation
from flask import request,jsonify,make_response
from flask_bcrypt import Bcrypt


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




if __name__  =="__main__":
    app.run (port =5555, debug =True)