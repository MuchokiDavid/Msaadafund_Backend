from models import User,Organisation,Account,Campaign,Donation
from flask_admin.contrib.sqla import  ModelView
# from flask_admin import AdminIndexView

class  UserAdminView(ModelView):
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
    column_labels=dict(accountType='Account Type',accountName= "Account Name", accountNumber='Account Number', orgId='Organization',)