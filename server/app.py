#Flask app
from flask import Flask
from flask_migrate import Migrate
from flask_restful import Api
from models import db, User, Donation, Withdraw, Campaign, Organisation


app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///msaada.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

migrate = Migrate(app, db)
db.init_app(app)
api = Api(app)





if __name__  =="__main__":
    app.run (port =5555, debug =True)