#seed data
from flask import Flask, session
from faker import Faker
from random import choice as rc
from flask_bcrypt import Bcrypt
import datetime
from datetime import datetime
from models import db, Campaign, User, Organisation, Donation,Transactions
from app import app

fake=Faker()
bcrypt= Bcrypt()

with app.app_context():
    print("Deleting data.......................")
    # db.session.query(User).delete()
    # db.session.query(Campaign).delete()
    # db.session.query(Organisation).delete()
    db.session.query(Donation).delete()
    db.session.query(Transactions).delete()
    db.session.commit()

    donations = [
        Donation(
            amount=500.00,
            currency='KES',
            donationDate=datetime(2024, 8, 10, 10, 30),
            donor_name='John Doe',
            user_id=1,  # Ensure this user exists in your database
            campaign_id=1,  # Ensure this campaign exists in your database
            status='Completed',
            invoice_id='INV123456',
            method='Credit Card',
            api_ref='API123456'
        ),
        Donation(
            amount=1500.00,
            currency='KES',
            donationDate=datetime(2024, 8, 11, 14, 45),
            donor_name='Jane Smith',
            user_id=2,  # Ensure this user exists in your database
            campaign_id=1,  # Ensure this campaign exists in your database
            status='Pending',
            invoice_id='INV654321',
            method='M-Pesa',
            api_ref='API654321'
        ),
        Donation(
            amount=750.00,
            currency='KES',
            donationDate=datetime(2024, 8, 12, 16, 00),
            donor_name='Alice Johnson',
            user_id=3,  # Ensure this user exists in your database
            campaign_id=1,  # Ensure this campaign exists in your database
            status='Completed',
            invoice_id='INV789123',
            method='PayPal',
            api_ref='API789123'
        ),
    ]

    # Add donations to the database
    db.session.add_all(donations)
    db.session.commit()
    print("Seed data added to the Donations table.")

    transactions = [
        Transactions(
            tracking_id='TXN123456',
            batch_status='Completed',
            trans_type='Credit',
            trans_status='Success',
            amount=1500.75,
            transaction_account_no='ACCT123456',
            request_ref_id='REQ123456',
            name='John Doe',
            acc_refence='REF123',
            narrative='Donation for Campaign A',
            transaction_date=datetime(2024, 8, 10, 14, 30),
            org_id='1',
            campaign_name='Campaign A',
            bank_code='1',
            signatory_status='Approved'
        ),
        Transactions(
            tracking_id='TXN123457',
            batch_status='Pending',
            trans_type='Debit',
            trans_status='Failed',
            amount=200.00,
            transaction_account_no='ACCT654321',
            request_ref_id='REQ654321',
            name='Jane Smith',
            narrative='Payment for Services',
            transaction_date=datetime(2024, 8, 11, 9, 45),
            org_id='1',
            campaign_name='Campaign B',
            bank_code='1',
            signatory_status='Pending'
        ),
        Transactions(
            tracking_id='TXN123458',
            batch_status='Completed',
            trans_type='Credit',
            trans_status='Success',
            amount=750.00,
            transaction_account_no='ACCT112233',
            request_ref_id='REQ112233',
            name='Alice Johnson',
            acc_refence='REF456',
            narrative='Contribution to Campaign C',
            transaction_date=datetime(2024, 8, 12, 16, 00),
            org_id='1',
            campaign_name='Campaign C',
            bank_code='BANK003',
            signatory_status='Approved'
        ),
    ]

    # Add transactions to the database
    db.session.add_all(transactions)
    db.session.commit()
    print("Seed data added to the Transactions table.")

#Seeding users
#     print("Seeding user........................")
#     users = [
#         {'firstName':'John',
#         'lastName':'Doe',
#         'username':'johndoe',
#         'email':'john@example.com',
#         'password':'hashedpassword1',
#         'nationalId':123456789,
#         'phoneNumber':'254234567890',
#         'isActive':False,
#         'address':'123 Main St, City'
#         },

#         {'firstName':'Jane',
#         'lastName':'Smith',
#         'username':'janesmith',
#         'email':'jane@example.com',
#         'password':'hashedpassword2',
#         'nationalId':987654321,
#         'phoneNumber':'254787654321',
#         'isActive':True,
#         'address':'456 Elm St Town'
#         }
#     ]

#     # def hash_pass(passwrd):
#     #     hash_password= bcrypt.generate_password_hash(passwrd).decode('utf-8')
#     #     return hash_password

#     for data in users :
#             user = User(
#                 firstName=data.get("firstName"), 
#                 lastName=data.get('lastName') ,
#                 username=data.get('username') ,
#                 email=data.get( "email") ,
#                 hashed_password=data.get('password'),
#                 nationalId=data.get('nationalId') ,
#                 phoneNumber=data.get('phoneNumber'),
#                 isActive=data.get('isActive') ,
#                 address=data.get('address')
#             )
#             db.session.add(user)
#             db.session.commit()
#     print("User added..........\n")

# #seed organisation
#     print("Start seeding organisation..............")
#     orgs = [
#         {'orgName':'UN',
#         'orgEmail':'charity@un.com',
#         'orgPassword':'hashedpassword1',
#         'orgPhoneNumber':'254721126928',
#         'orgAddress':'123 Main St, City',
#         'orgDescription': fake.sentence(nb_words=15)
#         },

#         {'orgName':'UNDP',
#         'orgEmail':'charity@undp.com',
#         'orgPassword':'hashedpassword2',
#         'orgPhoneNumber':'254723018212',
#         'orgAddress':'123 Tommboya St, City',
#         'orgDescription': fake.sentence(nb_words=15)
#         }
#     ]

#     for data in orgs:
#          org= Organisation(**data)
#          db.session.add(org)
#          db.session.commit()
#     print("Added successifully")

# #Seed donations
#     print("Start seeding donations..............")
#     donate = [
#         {'amount':100000.50,
#         'user_id': 1,
#         'campaign_id' : 1,
#         'status': 'PROCESSING',
#         "invoice_id": "RXX2E9D"
#         },

#         {'amount':float(100000),
#         'user_id': 2,
#         'campaign_id' : 1,
#         'status': 'PROCESSING',
#         "invoice_id": "RXX2E6R",
#         }
#     ]

#     for data in donate:
#          don= Donation(**data)
#          db.session.add(don)
#          db.session.commit()
#     print("Added successifully")

# #Seed campaign
#     print("Start seeding Campaigns.............")
#     camp1= Campaign (
#                     campaignName='AIDS',
#                     description='Fight against Aids',
#                     banner='https://img.freepik.com/free-photo/volunteer-holding-donate-box_23-2148687274.jpg?w=740&t=st=1711376202~exp=1711376802~hmac=a10082ac07c6a9fbccbd3f03d8628018fd4bef68e94064d860943faa1fbbece9',
#                     category='Health',
#                     startDate=datetime.date(2019,6,1),
#                     endDate= datetime.date(2020,12,31),
#                     targetAmount= float(1000000),
#                     isActive= True,
#                     walletId="VYBKPWY",
#                     org_id =1
#                 )
#     db.session.add(camp1)
#     db.session.commit()
#     print('Campaign added successfully')


    
