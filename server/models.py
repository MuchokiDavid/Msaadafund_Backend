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
    serialize_rules = ('-donations.user',)

    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100))
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)
    nationalId = db.Column(db.Integer, unique=True, nullable=False)
    phoneNumber = db.Column(db.String, unique=True)
    isActive = db.Column(db.Boolean(), default=True)
    address = db.Column(db.String(), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)
    donations =db.relationship('Donation', backref='user')
    

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
        return f"ID:{self.id} First Name :{self.firstName} Last Name :{self.lastName} Username:{self.username} Email:{self.email} Phone Number:{self.phoneNumber} National ID:{self.nationalId} Active:{self.isActive} Address:{self.address}"
    

class Organisation(db.Model, SerializerMixin):
    __tablename__ = 'organisations'
    serialize_rules = ('-campaigns.organisation',)

    id = db.Column(db.Integer, primary_key=True)
    orgName = db.Column(db.String(64), unique=True, nullable = False)
    orgEmail = db.Column(db.String(254), unique=True, nullable=False)
    orgPassword =db.Column(db.String(128), nullable=False)
    orgAddress = db.Column(db.String(), nullable = False)
    orgPhoneNumber = db.Column(db.String(),unique=True)
    orgDescription = db.Column (db.String())
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable = True)
    campaigns = db.relationship('Campaign', backref='organisation')
    accounts= db.relationship('Account', backref= 'organisation')

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
        return f"ID:{self.id} Organisation Name:{self.orgName}  Organisation Email:{self.orgEmail} Organisation Phone Number:{self.orgPhoneNumber} Organisation Address:{self.orgAddress} Organisation Description:{self.orgDescription} Organisation Created At:{self.created_at}"
     
    def serialize(self):
        return {
            "id": self.id,
            "orgName": self.orgName,
            "orgEmail": self.orgEmail,
            "orgPhoneNumber": self.orgPhoneNumber,
            "orgAddress": self.orgAddress,
            "orgDescription": self.orgDescription,
            "created_at": self.created_at.strftime("%Y-%m-%d ")
        }

#Account model  for organisation accounts to withdraw money to
class Account(db.Model, SerializerMixin):
    __tablename__=  'accounts'
    id = db.Column(db.Integer, primary_key=True)
    accountType = db.Column(db.String)
    accountNumber= db.Column(db.String, unique=True)
    orgId = db.Column(db.Integer, db.ForeignKey('organisations.id'),nullable=False)

    def serialize(self):
        """ Serialize the object into a dictionary"""
        return {
                'id': self.id,
                'accountType': self.accountType,
                'accountNumber': self.accountNumber,
                'orgId': self.orgId
               }
    def __repr__(self):
        return  f'Account: {self.accountNumber} Account_Type: {self.accountType}, Org ID: {self.orgId}'

class Donation (db.Model, SerializerMixin):
    __tablename__ = 'donations'
    serialize_rules =('-user.donations','-campaign.donations')
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float,nullable=False)
    donationDate = db.Column(db.DateTime, server_default=db.func.now())
    user_id =  db.Column(db.Integer, db.ForeignKey('users.id'))
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now(), nullable=True)

    def serialize(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'donationDate': self.donationDate,
            'userId': self.user_id,
            'campaignId': self.endDate,
        }
    
    def __repr__(self):
        return f"ID:{self.id} Amount:{self.amount} Date:{self.donationDate} User ID:{self.user_id} Campaign ID:{self.campaign_id}"



class  Campaign(db.Model, SerializerMixin):
    __tablename__='campaigns'
    serialize_rules =('-organisation.campaigns','-donations.campaign')
    id = db.Column(db.Integer, primary_key =True)
    campaignName = db.Column(db.String())
    description = db.Column(db.String())
    category= db.Column(db.String())
    banner = db.Column(db.String(255), unique=False)
    startDate = db.Column (db.String())
    endDate = db.Column(db.String())
    targetAmount = db.Column(db.Float())
    isActive = db.Column(db.Boolean(), default=True)
    walletId = db.Column (db.String(), unique =True)
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
            'startDate': self.startDate,
            'endDate': self.endDate,
            'targetAmount': self.targetAmount,
            'isActive': self.isActive,
            'walletId': self.walletId,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'org_id': self.org_id,
            'donations': [donation.serialize() for donation in self.donations]
        }

    def __repr__ (self):
        return f"ID: {self.id} Campaign Name: {self.campaignName}  Description: {self.description} Category:{self.category} Start Date : {self.startDate} End Date:{self.endDate} Target Amount :{self.targetAmount} Wallet ID :{self.walletId} Organisation ID:{self.org_id}"


# class Withdraw (db.Model, SerializerMixin):
#     __tablename__="withdrawals"
#     serialize_rules =('-campaign.withdrawals')
#     id = db.Column(db.Integer, primary_key= True)
#     amount = db.Column(db.Float, nullable= False)
#     status = db.Column(db.String())
#     withdraw_method = db.Column(db.String())
#     intasend_id =  db.Column(db.String())
#     transaction_date = db.Column(db.DateTime, server_default=db.func.now())
#     campaign_id = db.Column(db.Integer, db.ForeignKey("campaigns.id"))

    
#     def __repr__(self):
#         return f"Id:'{self.id} Amount: {self.amount} Status: {self.status} Withdraw_method:{self.withdraw_method} Intasend_id:{self.intasend_id} Transaction_date:{self.transaction_date} Campaign_id: {self.campaign_id}"
    
class TokenBlocklist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    jti = db.Column(db.String(), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__ (self):
        return f"<token {self.jti}>"