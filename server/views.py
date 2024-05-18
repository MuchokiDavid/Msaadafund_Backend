from models import User,db, bcrypt
from flask_admin.contrib.sqla import  ModelView
# from flask import render_template,request,redirect,url_for,jsonify,Blueprint
# from flask_login import LoginManager,current_user, UserMixin, login_user, logout_user, login_required

# view_bp = Blueprint('view', __name__, template_folder='templates')

# login_manager = LoginManager(view_bp)
# login_manager.login_view = 'login'
# # login_manager= LoginManager(app)
# # login_manager.login_view= 'login'

# class UserLogin(UserMixin):
#     pass

# @login_manager.user_loader
# def load_user(user_id):
#     return User.query.get(user_id)
    
# @view_bp.route('/register', methods=['GET,POST'])
# def register():
#     if request.method=='POST':
#         username = request.form['username']
#         firstName = request.form['firstName']
#         lastName = request.form['lastName']
#         email = request.form['email']
#         nationalId = request.form['nationalId']
#         role= "Admin"
#         phoneNumber = request.form['phoneNumber']
#         address = request.form['address']
#         hashed_password = request.form['password']

#         if not all([firstName, lastName, username, email, nationalId, phoneNumber, address, hashed_password]):
#             return jsonify({"error": "Missing required fields"}), 400

#         # Checking for existing user data
#         existing_user = User.query.filter_by(username=username).first()
#         if existing_user:
#             return jsonify({"error": "Username already exists"}), 400

#         existing_email = User.query.filter_by(email=email).first()
#         if existing_email:
#             return jsonify({"error": "Email already exists"}), 400

#         existing_national_id = User.query.filter_by(nationalId=nationalId).first()
#         if existing_national_id:
#             return jsonify({"error": "National ID already exists"}), 400

#         existing_phone_number = User.query.filter_by(phoneNumber=phoneNumber).first()
#         if existing_phone_number:
#             return jsonify({"error": "Phone number already exists"}), 404

#         new_admin=User(username=username,
#                        firstName=firstName,
#                        lastName=lastName,
#                        email=email,
#                        nationalId=nationalId,
#                        role=role,
#                        phoneNumber=phoneNumber,
#                        address=address, 
#                        password=hashed_password)
#         db.session.add(new_admin)
#         db.session.commit()
#         return redirect(url_for('login'))

#     return render_template('register.html')
   
    
# @view_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         # Authenticate the user and log them in
#         if request.method == 'POST':
#             user = User.query.filter_by(username=request.form['username']).first()
#             if user and bcrypt.check_password_hash(user.password, request.form['password']):
#                 # login_user(user)
#                 # return {"message":"success"}
#                 return redirect(url_for('index.html'))
#     # return render_template('login.html')

# @view_bp.route('/admin/logout')
# @login_required
# def logout():
#     logout_user()
#     return redirect(url_for('login'))

class  UserAdminView(ModelView):
#     def is_accessible(self):
#         return not current_user.is_authenticated and current_user.role == 'Admin'
    column_sortable_list=('created_at','firstName','lastName')
    column_searchable_list = ('firstName','lastName','username','email','phoneNumber','nationalId', 'role')
    column_list=('id','firstName','lastName','username','email','phoneNumber','nationalId','address','isActive', 'role','created_at')
    column_labels=dict(name= 'Name',username='Username',email="Email",isActive = 'isActive', role ='Role')
    column_filters=column_list

class  OrganisationAdminView(ModelView):
    column_sortable_list=('created_at','orgName')
    column_searchable_list= ('orgName','orgEmail','orgAddress','orgDescription')
    column_list=('id','orgName','orgEmail','orgType','orgAddress','orgDescription','website_link','youtube_link','isVerified','created_at')
    column_labels=dict(orgName='Organization Name', orgEmail='Email',orgType='Category',orgAddress='Office Address',orgDescription='Description',website_link= 'Website',youtube_link='Youtube', created_at='Created On')
    column_filters=('orgName','orgEmail','orgAddress','orgDescription','isVerified')

class DonationAdminView(ModelView):
    column_sortable_list=('amount','created_at','donationDate','status','currency')
    column_searchable_list=('campaign_id','user_id','donationDate')
    column_list=('id','user_id','donor_name','amount','currency','donationDate','campaign_id','status','invoice_id','api_ref','created_at')
    column_labels=dict(user_id='User Id', amount='Amount', donor_name='Donor Name',currency='Currency', donationDate='Donation Date',status='Status',invoice_id='Invoice',api_ref='API Ref',created_at='Created At')
    column_filters=column_list

class CampaignAdminView(ModelView):
    column_sortable_list=('created_at', 'campaignName', 'featured','category')
    column_searchable_list=('campaignName', 'startDate','org_id')
    column_list=('id','campaignName','category','targetAmount','org_id', 'isActive','startDate', 'endDate','description','youtube_link','walletId','featured','created_at', 'updated_at')
    column_labels=dict(campaignName='Campaign Name',category='Category',targetAmount='Budget', org_id='Organization', isActive='Active',startDate='Start Date', endDate='End Date',walletId ='WalletId',description='Description', youtube_link='Youtube', featured='Featured', created_at='Created On', updated_at='Updated On')
    column_filters=('campaignName', 'startDate', 'endDate', 'targetAmount', 'org_id', 'isActive', 'featured')

class AccountAdminView(ModelView):
    column_sortable_list=('providers','accountNumber')
    column_searchable_list=('providers','accountNumber')
    column_list=('id','providers','accountNumber','orgId')
    column_labels=dict(providers='Provider', accountNumber='Account Number', orgId='Organization')
    column_filters=column_sortable_list

class TransactionAdminView(ModelView):
    column_sortable_list=('transaction_date', 'amount', 'trans_type', 'org_id', 'trans_status')
    column_searchable_list=('transaction_date', 'amount', 'trans_type', 'org_id', 'trans_status')
    column_list=('id','tracking_id','batch_status', 'transaction_date', 'amount', 'trans_type','trans_status', 'org_id', 'campaign_name', 'created_at')
    column_labels=dict(tracking_id='Tracking Id', batch_status='Batch Status', transaction_date='Transaction Date', amount='Amount', trans_type='Transaction Type', trans_status='Transaction Status', org_id='Organization', campaign_name='Campaign Name', created_at='Created On')
    column_filters=column_list