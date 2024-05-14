#ORM
import datetime 
import bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from sqlalchemy.orm import validates
from sqlalchemy.ext.hybrid import hybrid_property
from flask_bcrypt import Bcrypt
import re

db = SQLAlchemy()
bcrypt = Bcrypt()
class User(db.Model, SerializerMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    nationalId = db.Column(db.Integer)
    phoneNumber = db.Column(db.String, unique=True,nullable=False)
    isActive = db.Column(db.Boolean(), default=True)
    address = db.Column(db.String())
    role= db.Column(db.String(), default= 'User', nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)
    donations =db.relationship('Donation', backref='user')
    subscriptions = db.relationship('Subscription',backref='user')
    

    @validates('phoneNumber')
    def validate_phone_number(self, key, number):
        if not number.isdigit() or len(number) != 12:
            return "Phone Number must be a 12-digit number"
        return number
    
    @validates('email')
    def validate_fields(self, key, value):
        if not re.match("[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("E-mail not valid!!")
        return value

     # Password getter and setter methods
    @hybrid_property
    def password(self):
        return self.hashed_password

    @password.setter
    def password(self, plain_text_password):
        self.hashed_password = bcrypt.generate_password_hash(
            plain_text_password.encode('utf-8')).decode('utf-8')

    def check_password(self, attempted_password):
        return bcrypt.check_password_hash(self.hashed_password, attempted_password.encode('utf-8'))
    
    def serialize(self):
        return {
            'id': self.id,
            'firstName': self.firstName,
            'lastName': self.lastName,
            'username': self.username,
            'email': self.email,
            'nationalId': self.nationalId,
            'phoneNumber': self.phoneNumber,
            'isActive': self.isActive,
            'role': self.role,
            'address': self.address,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'donations': [donation.serialize() for donation in self.donations],
            "subscriptions":[sub.serialize() for sub in self.subscriptions]

        }
    def __repr__ (self):
        return f"ID:{self.id} FirstName:{self.firstName}, LastName:{self.lastName},  Username:{self.username},  Email:{self.email}, Phone Number:{self.phoneNumber}"

class Organisation(db.Model, SerializerMixin):
    __tablename__ = 'organisations'

    id = db.Column(db.Integer, primary_key=True)
    orgName = db.Column(db.String(64), unique=True, nullable = False)
    orgEmail = db.Column(db.String(254), unique=True, nullable=False)
    orgPassword =db.Column(db.String(128), nullable=False)
    orgAddress = db.Column(db.String(), nullable = False)
    orgType = db.Column(db.String())
    orgPhoneNumber = db.Column(db.String(),unique=True)
    profileImage = db.Column(db.String())
    orgDescription = db.Column (db.String())
    youtube_link = db.Column(db.String())
    isVerified= db.Column(db.Boolean(), default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable = True)
    campaigns = db.relationship('Campaign', backref='organisation')
    accounts= db.relationship('Account', backref= 'organisation')
    subscriptions = db.relationship('Subscription',backref='organisation')

    @validates('orgPhoneNumber')
    def validate_phone_number(self, key, number):
        if not number.isdigit() or len(number) != 12:
            return "Phone Number must be a 12-digit number"
        return number
    
    @validates('orgEmail')
    def validate_fields(self, key, value):
        if not re.match("[^@]+@[^@]+\.[^@]+", value):
            raise ValueError("E-mail not valid!!")
        return value

    # Password getter and setter methods
    @hybrid_property
    def password(self):
        return self.orgPassword

    @password.setter
    def password(self, plain_text_password):
        self.orgPassword = bcrypt.generate_password_hash(
            plain_text_password.encode('utf-8')).decode('utf-8')

    def check_password(self, attempted_password):
        return bcrypt.check_password_hash(self.orgPassword, attempted_password.encode('utf-8'))
    
    def __repr__ (self):
        return f"ID:{self.id} Organisation Name:{self.orgName},  Organisation Email:{self.orgEmail}, Organisation Phone Number:{self.orgPhoneNumber}, Organisation Address:{self.orgAddress}, Profile Image:{self.profileImage} ,Organisation Description:{self.orgDescription}, isVerified:{self.isVerified}, Organisation Created At:{self.created_at}"
     
    def serialize(self):
        return {
            "id": self.id,
            "orgName": self.orgName,
            "orgEmail": self.orgEmail,
            "orgPhoneNumber": self.orgPhoneNumber,
            "orgAddress": self.orgAddress,
            "orgType": self.orgType,
            "isVerified":self.isVerified,
            "profileImage": self.profileImage,
            "orgDescription": self.orgDescription,
            "youtube_link": self.youtube_link,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "campaigns": [camp.serialize() for camp in self.campaigns],
            "accounts": [acc.serialize() for acc in self.accounts],
            "subscriptions":[sub.serialize() for sub in self.subscriptions]
        }


# Account model  for organisation accounts to withdraw money to
class Account(db.Model, SerializerMixin):
    __tablename__=  'accounts'

    id = db.Column(db.Integer, primary_key=True)
    providers = db.Column(db.String, nullable=False)
    accountName = db.Column(db.String, nullable=False)
    accountNumber = db.Column(db.String, unique=True, nullable=False)
    hashed_pin = db.Column(db.String(8), nullable=False)
    orgId = db.Column(db.Integer, db.ForeignKey('organisations.id'), nullable=False)

    @hybrid_property
    def pin(self):
        return self.hashed_pin

    @pin.setter
    def pin(self, plain_text_pin):
        self.hashed_pin = bcrypt.generate_password_hash(
            plain_text_pin.encode('utf-8')).decode('utf-8')

    def check_pin(self, attempted_pin):
        return bcrypt.check_password_hash(self.hashed_pin, attempted_pin.encode('utf-8'))

    def __repr__(self):
        return f'Account: {self.accountNumber}, Provider: {self.providers}, Org ID: {self.orgId}'

    def serialize(self):
        return {
            'id': self.id,
            'accountName':self.accountName,
            'accountNumber': self.accountNumber,
            'providers': self.providers,
            'orgId': self.orgId
        }
    
class Donation (db.Model, SerializerMixin):
    __tablename__ = 'donations'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float,nullable=False)
    donationDate = db.Column(db.DateTime, server_default=db.func.now())
    donor_name= db.Column(db.String, nullable = True)
    user_id =  db.Column(db.Integer, db.ForeignKey('users.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    status= db.Column(db.String, nullable=False)
    invoice_id=db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'donationDate': self.donationDate.strftime("%Y-%m-%d"),
            'donor_name': self.donor_name,
            'userId': self.user_id,
            'campaignId': self.campaign_id,
            'campaign': {
                'id': self.campaign.id,
                'campaignName': self.campaign.campaignName,
                'description': self.campaign.description,
                'category': self.campaign.category,
                'banner': self.campaign.banner,
                'startDate': self.campaign.startDate,
                'endDate': self.campaign.endDate,
                'targetAmount': self.campaign.targetAmount,
                'isActive': self.campaign.isActive,
                'walletId': self.campaign.walletId,
                'featured': self.campaign.featured,
                'created_at': self.campaign.created_at.isoformat() if self.campaign.created_at else None,
                'updated_at': self.campaign.updated_at.isoformat() if self.campaign.updated_at else None,
                'org_id': self.campaign.org_id,
                'organisation': {
                    'id': self.campaign.organisation.id,
                    'orgName': self.campaign.organisation.orgName,
                    'orgEmail': self.campaign.organisation.orgEmail,
                    'orgAddress': self.campaign.organisation.orgAddress,
                    'orgType': self.campaign.organisation.orgType,
                    'orgPhoneNumber': self.campaign.organisation.orgPhoneNumber,
                    "profileImage": self.campaign.organisation.profileImage,
                    'orgDescription': self.campaign.organisation.orgDescription,
                    'isVerified': self.campaign.organisation.isVerified,
                }
            },
            'status': self.status,
            'invoice_id':self.invoice_id
        }
    
    def __repr__(self):
        return f"ID:{self.id} Amount:{self.amount}, Date:{self.donationDate}, Donor Name:{self.donor_name}, User ID:{self.user_id}, Campaign ID:{self.campaign_id}"



class  Campaign(db.Model, SerializerMixin):
    __tablename__='campaigns'
    
    id = db.Column(db.Integer, primary_key =True)
    campaignName = db.Column(db.String(),nullable=False,unique=True)
    description = db.Column(db.String(),nullable=False)
    category= db.Column(db.String(),nullable=False)
    banner = db.Column(db.String(255), unique=False)
    youtube_link = db.Column(db.String(), nullable=True)
    startDate = db.Column (db.String(),nullable=False)
    endDate = db.Column(db.String(),nullable=False)
    targetAmount = db.Column(db.Float(),nullable=False)
    isActive = db.Column(db.Boolean(), default=True)
    walletId = db.Column (db.String(), unique =True,nullable=False)
    featured=db.Column(db.Boolean(), default= False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)
    org_id = db.Column(db.String(), db.ForeignKey('organisations.id'))
    # withdrawals = db.relationship('Withdraw', backref='campaign'), Serial_rule: '-withdrawals.campaign',
    donations =db.relationship('Donation', backref='campaign')

    def serialize(self):
        return {
            'id': self.id,
            'campaignName': self.campaignName,
            'description': self.description,
            'category': self.category,
            'banner': self.banner,
            'youtube_link': self.youtube_link,
            'startDate': self.startDate,
            'endDate': self.endDate,
            'targetAmount': self.targetAmount,
            'isActive': self.isActive,
            'walletId': self.walletId,
            'featured': self.featured,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'org_id': self.org_id,
            'organisation': {
            'id': self.organisation.id,
            'orgName': self.organisation.orgName,
            'orgEmail': self.organisation.orgEmail,
            'orgAddress': self.organisation.orgAddress,
            'orgType': self.organisation.orgType,
            'orgPhoneNumber': self.organisation.orgPhoneNumber,
            "profileImage": self.organisation.profileImage,
            'orgDescription': self.organisation.orgDescription,
            'isVerified': self.organisation.isVerified,
            },
            'donations': [donation.serialize() for donation in self.donations]
        }

    def __repr__ (self):
        return f"ID: {self.id}, Campaign Name: {self.campaignName},  Description: {self.description}, Category:{self.category}, Start Date : {self.startDate}, End Date:{self.endDate}, Target Amount :{self.targetAmount}, Wallet ID :{self.walletId}, Organisation ID:{self.org_id}"

class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__ (self):
        return f"<token {self.jti}>"
    
class Enquiry(db.Model):
    __tablename__="enquiries"
    id= db.Column(db.Integer, primary_key= True)
    name= db.Column(db.String())
    email= db.Column(db.String())
    subject= db.Column(db.String())
    message= db.Column(db.String())
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"name: {self.name} email: {self.email} subject: {self.subject}"
    
class Transactions(db.Model):
    __tablename__="transactions"
    id= db.Column(db.Integer, primary_key= True)

    tracking_id= db.Column(db.String())
    batch_status= db.Column(db.String)
    trans_type= db.Column(db.String)
    trans_status= db.Column(db.String)
    amount= db.Column(db.Float)
    transaction_account_no= db.Column(db.String)
    request_ref_id= db.Column(db.String)
    org_name= db.Column(db.String)
    transaction_date = db.Column(db.DateTime, server_default=db.func.now())#Intasend created at
    org_id= db.Column(db.String())
    campaign_name = db.Column(db.String)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'tracking_id': self.tracking_id,
            'batch_status': self.batch_status,
            'trans_type': self.trans_type,
            'trans_status': self.trans_status,
            'amount': self.amount,
            'transaction_account_no': self.transaction_account_no,
            'request_ref_id': self.request_ref_id,
            'org_name': self.org_name,
            'transaction_date': self.transaction_date,
            'org_id': self.org_id,
            'campaign_name': self.campaign_name,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    def __repr__(self):
        return f"ID: {self.id}, Tracking ID: {self.tracking_id}, Batch Status: {self.batch_status}, Transaction Type: {self.trans_type}, Transaction Status: {self.trans_status}, Amount: {self.amount}, Transaction Account No: {self.transaction_account_no}, Request Ref ID: {self.request_ref_id}, Org Name: {self.org_name}, Transaction Date: {self.transaction_date}, Org ID: {self.org_id}, Campaign Name: {self.campaign_name}"
    
    # subscriptions
class Subscription(db.Model,SerializerMixin):
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    organisation_id = db.Column(db.Integer, db.ForeignKey('organisations.id'))

    def serialize(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'organisation_id': self.organisation_id,
            'organisation': {
                'id': self.organisation.id,
                'orgName': self.organisation.orgName,
                'orgEmail': self.organisation.orgEmail,
                'orgAddress': self.organisation.orgAddress,
                'orgType': self.organisation.orgType,
                'orgPhoneNumber': self.organisation.orgPhoneNumber,
                "profileImage": self.organisation.profileImage,
                'orgDescription': self.organisation.orgDescription,
                'isVerified': self.organisation.isVerified,
            },
            'user':{
                'id': self.user.id,
                'username': self.user.username,
                'firstName': self.user.firstName,
                'lastName': self.user.lastName,
                'email': self.user.email,
                'phoneNumber': self.user.phoneNumber,
            }
        }


    

    def __repr__(self):
        return f"Subscription: {self.id}, User ID: {self.user_id}, Organisation ID: {self.organisation_id}"