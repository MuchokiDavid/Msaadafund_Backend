from models import User,db, bcrypt
from flask_admin.contrib.sqla import  ModelView
from flask import render_template,request,redirect,url_for,jsonify
from app import app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


login_manager= LoginManager(app)
login_manager.login_view= 'login'

class UserLogin(UserMixin):
    pass

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/admin/register', methods=['POST'])
def register():
    if request.method=='POST':
        username = request.form['username']
        firstName = request.form['firstName']
        lastName = request.form['lastName']
        username = request.form['username']
        email = request.form['email']
        nationalId = request.form['nationalId']
        role= "Admin"
        phoneNumber = request.form['phoneNumber']
        address = request.form['address']
        hashed_password = request.form['password']

        if not all([firstName, lastName, username, email, nationalId, phoneNumber, address, hashed_password]):
            return jsonify({"error": "Missing required fields"}), 400

        # Checking for existing user data
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 400

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            return jsonify({"error": "Email already exists"}), 400

        existing_national_id = User.query.filter_by(nationalId=nationalId).first()
        if existing_national_id:
            return jsonify({"error": "National ID already exists"}), 400

        existing_phone_number = User.query.filter_by(phoneNumber=phoneNumber).first()
        if existing_phone_number:
            return jsonify({"error": "Phone number already exists"}), 404

        new_admin=User(username=username,
                       firstname=firstName,
                       lastname=lastName,
                       email=email,
                       nationalId=nationalId,
                       role=role,
                       phoneNumber=phoneNumber,
                       address=address, 
                       password=hashed_password)
        db.session.add(new_admin)
        db.session.commit()
        return redirect(url_for('login'))
    
@app.route('/admin/login', methods=['GET', 'POST'])
def login():
    from models import bcrypt
    if request.method == 'POST':
        # Authenticate the user and log them in
        if request.method == 'POST':
            user = User.query.filter_by(username=request.form['username']).first()
            if user and bcrypt.check_password_hash(user.password, request.form['password']):
                login_user(user)
                return redirect(url_for('admin.index'))
    return render_template('login.html')

@app.route('/admin/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

class  UserAdminView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.role == 'Admin'
    
    column_sortable_list=('created_at','firstName','lastName')
    column_searchable_list = ('firstName','lastName','username','email','phoneNumber','nationalId', 'role')
    column_list=('firstName','lastName','username','email','phoneNumber','nationalId','address', 'role','created_at')
    # column_labels=dict(name= 'Name',username='Username',email="Email", role ='Role')
    column_filters=column_list

class  OrganisationAdminView(ModelView):
    column_sortable_list=('created_at','orgName')
    column_searchable_list= ('orgName','orgEmail','orgAddress','orgDescription')
    column_list=('orgName','orgEmail','orgAddress','orgDescription','isVerified','created_at')
    column_labels=dict(orgName='Organization Name', orgEmail='Email',orgAddress='Office Address',orgDescription='Description', created_at='Created On')
    column_filters=('orgName','orgEmail','orgAddress','orgDescription','isVerified')

class DonationAdminView(ModelView):
    column_sortable_list=('amount','created_at','donationDate')
    column_searchable_list=('campaign_id','user_id','donationDate')
    column_list=('user_id','amount','donationDate','campaign_id', 'created_at')
    column_labels=dict(user_id='User Id', amount='Amount', donationDate='Donation Date', created_at='Created At')
    column_filters=column_list

class CampaignAdminView(ModelView):
    column_sortable_list=('created_at', 'campaignName')
    column_searchable_list=('campaignName', 'startDate','org_id')
    column_list=('campaignName','targetAmount','org_id', 'isActive','startDate', 'endDate','description','walletId','created_at')
    column_labels=dict(campaignName='Campaign Name',targetAmount='Budget', org_id='Organization', isActive='Active',startDate='Start Date', endDate='End Date',walletId ='WalletId',description='Description', created_at='Created On')
    column_filters=('campaignName', 'startDate', 'endDate', 'targetAmount', 'org_id', 'isActive')

class AccountAdminView(ModelView):
    column_sortable_list=('accountType','accountNumber','accountName')
    column_searchable_list=('accountNumber','accountName','accountNumber')
    column_list=('accountType','accountName','accountNumber','orgId')
    column_labels=dict(accountType='Account Type',accountName= "Account Name", accountNumber='Account Number', orgId='Organization')
    column_filters=column_sortable_list