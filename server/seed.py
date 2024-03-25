#seed data
from flask import Flask, session
from faker import Faker
from random import choice as rc
from flask_bcrypt import Bcrypt
import datetime
from models import db, Campaign, User, Organisation, Donation
from app import app

fake=Faker()
bcrypt= Bcrypt()

with app.app_context():
    print("Deleting data.......................")
    db.session.query(User).delete()
    db.session.query(Campaign).delete()
    db.session.query(Organisation).delete()
    db.session.query(Donation).delete()

#Seeding users
    print("Seeding user........................")
    users = [
        {'firstName':'John',
        'lastName':'Doe',
        'username':'johndoe',
        'email':'john@example.com',
        'password':'hashedpassword1',
        'nationalId':123456789,
        'phoneNumber':'254234567890',
        'isActive':False,
        'address':'123 Main St, City'
        },

        {'firstName':'Jane',
        'lastName':'Smith',
        'username':'janesmith',
        'email':'jane@example.com',
        'password':'hashedpassword2',
        'nationalId':987654321,
        'phoneNumber':'254787654321',
        'isActive':True,
        'address':'456 Elm St Town'
        }
    ]

    def hash_pass(passwrd):
        hash_password= bcrypt.generate_password_hash(passwrd).decode('utf-8')
        return hash_password

    for data in users :
            user = User(
                firstName=data.get("firstName"), 
                lastName=data.get('lastName') ,
                username=data.get('username') ,
                email=data.get( "email") ,
                hashed_password=hash_pass(data.get('password') ),
                nationalId=data.get('nationalId') ,
                phoneNumber=data.get('phoneNumber'),
                isActive=data.get('isActive') ,
                address=data.get('address')
            )
            db.session.add(user)
            db.session.commit()
    print("User added..........\n")

#seed organisation
    print("Start seeding organisation..............")
    orgs = [
        {'orgName':'UN',
        'orgEmail':'charity@un.com',
        'orgPassword':hash_pass('hashedpassword1'),
        'orgPhoneNumber':'254721126928',
        'orgAddress':'123 Main St, City',
        'orgDescription': fake.sentence(nb_words=15)
        },

        {'orgName':'UNDP',
        'orgEmail':'charity@undp.com',
        'orgPassword':hash_pass('hashedpassword2'),
        'orgPhoneNumber':'254723018212',
        'orgAddress':'123 Tommboya St, City',
        'orgDescription': fake.sentence(nb_words=15)
        }
    ]

    for data in orgs:
         org= Organisation(**data)
         db.session.add(org)
         db.session.commit()
    print("Added successifully")

#Seed donations
    print("Start seeding donations..............")
    donate = [
        {'amount':100000.50,
        'user_id': 1,
        'campaign_id' : 1
        },

        {'amount':float(100000),
        'user_id': 2,
        'campaign_id' : 1
        }
    ]

    for data in donate:
         don= Donation(**data)
         db.session.add(don)
         db.session.commit()
    print("Added successifully")

#Seed campaign
    print("Start seeding Campaigns.............")
    camp1= Campaign (
                    campaignName='AIDS',
                    description='Fight against Aids',
                    banner='https://img.freepik.com/free-photo/volunteer-holding-donate-box_23-2148687274.jpg?w=740&t=st=1711376202~exp=1711376802~hmac=a10082ac07c6a9fbccbd3f03d8628018fd4bef68e94064d860943faa1fbbece9',
                    startDate=datetime.date(2019,6,1),
                    endDate= datetime.date(2020,12,31),
                    targetAmount= float(1000000),
                    isActive= True,
                    walletId="ZQM85LQ",
                    org_id =1
                )
    db.session.add(camp1)
    db.session.commit()
    print('Campaign added successfully')

    
