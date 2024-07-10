#helper function

#function to check wallet balance
import random
import string
from flask_mail import Message
from flask import jsonify
import os
from dotenv import load_dotenv
load_dotenv()
# from app import token, publishable_key,service
from intasend import APIService
from models import Campaign



token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
service = APIService(token=token,publishable_key=publishable_key, test=True)

def check_wallet_balance(wallet_id):
    try:
        response = service.wallets.details(wallet_id)
        if response.get('errors'):
            error_message= response.get('errors')[0].get('detail')
            return jsonify({'Error':error_message})
        available_balance= response.get('available_balance')
        print(available_balance)
        return available_balance
    except Exception as e:
        return jsonify({'error': "error retrieving wallet"}), 500
    
class sendMail():
    #Send mail after donation has completed successifully
    def send_mail_on_donation_completion(amount,date,name,campaign,email,organisation):
        from app import mail
        subject = f"Donation to {campaign} by {organisation} was successful"
        body = f"Dear {name},\n\n Thank you for donating to {campaign} campaign on {date}.\nYour contribution is highly appreciated as it is used to make an impact in our community\n\n Best regards,\n {organisation}"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    #Send mail if the donation was not successiful
    def send_mail_donation_not_successiful(amount,date,name,campaign,email,organisation):
        print(email)
        from app import mail
        subject = f"Donation to {campaign} failed"
        body = f"Dear {name},\n\nUnfortunately your contribution to {campaign} campaign on {date} was not successiful. Please try again\n\n Best regards,\n {organisation}"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    #Send mail after withdrawal has completed successifully
    def send_mail_on_successiful_withdrawal(amount, date, name, campaign, email, organisation):
        from app import mail
        subject = "Withdrawal successful"
        body = f"Dear {name},\n\n Thank you for withdrawing from {campaign} campaign on {date}.\nYour withdrawal is highly appreciated as it is used to make an impact in our community\n\n Best regards,\n {organisation}"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    #Function to send enquiry mail
    def send_enquiry_mail(recipients,message,subject,from_email,name):
        from app import mail
        try:
            subject = subject
            body = f"{message}\n\nRegards\n{name}\n{from_email}\nWebsite"
            mail.send_message(subject=subject, recipients=recipients, body=body)
            return jsonify({"message": "Message sent successfully!"}), 200
        except Exception as e:
            print(e)
            return jsonify({"error": "Error sending the Message! Please try again later."}), 400
    
    #send mail after a campaign has been created
    def send_post_campaign(organisation, campaignName, description, category, targetAmount, startDate, endDate):
        from app import mail
        existing_campaign = Campaign.query.filter_by(campaignName=campaignName).first()
        url = f"https://www.msaadafund.com/campaigns/{existing_campaign.id}" #update once deployed 
        subject = f"{campaignName.upper()} Created Successfully"
        
        html_body = f"""
            <p>Hello {organisation.orgName}!</p>
            <p>You have successfully created a campaign.</p>
            <p><strong>Campaign Name:</strong> {campaignName}</p>
            <p><strong>Description:</strong> {description}</p>
            <p><strong>Category:</strong> {category}</p>
            <p><strong>Your target amount is Ksh:</strong> {targetAmount}</p>
            <p><strong>Start Date:</strong> {startDate}</p>
            <p><strong>End Date:</strong> {endDate}</p>
            <p><strong>Campaign link:</strong> <a href="{url}">{url}</a></p>
            <p>Good luck with your campaign!</p>
        """

        # mail.send_message(subject=subject, recipients=[organisation.orgEmail], body=body)
        msg = Message(subject, recipients=[organisation.orgEmail])
        msg.html = html_body
        mail.send(msg)

    
    #Function to send verification to organisation
    def send_org_verification_mail(org):
        from app import mail
        subject = "Welcome to MsaadaFund"
        body = f"Dear {org.orgName},\n\n Thank you for registering on our MsaadaFund Platform.\nYour account is not verified. Please reply to this email for verification\n\n Best regards,\n MsaadaFund Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    #Org registration mail
    def send_registration_email(org_email, org_name):
        from app import mail
        subject = "Organization Registration Confirmation"
        body = f"Hello: {org_name},\n\nThank you for registering on our MsaadaFund Platform.\n\nTo complete your registration and begin using our services, Please contact our support team for verification. This step is necessary to ensure the integrity and security of our platform.\n\nWe appreciate your cooperation and look forward to assisting you.\n\nRegards,\nMsaadaFund Team"
        
        try:
            mail.send_message(subject=subject, recipients=[org_email], body=body)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    #Function to send users email after sign up
    def send_user_signup_mail(user):
        from app import mail
        subject = "Welcome to MsaadaFund"
        body = f"Dear {user.firstName} {user.lastName},\n\n Thank you for registering on our MsaadaFund Platform.\n\n Best regards,\n MsaadaFund Team"
        recipients = [user.email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # send subscriptions
    def send_subscription_email(email,user,org_name):
        from app import mail
        subject = f"Subscription to {org_name.upper()}"
        body = f"Dear {user},\n\nWe're excited to inform you that you've successfully subscribed to receive updates on {org_name.upper()} latest campaigns and initiatives.\n\nYou're now part of our community dedicated to making a positive impact..\n\nBest regards,\nMsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_subscribers_createCampaign(email,user,campaignName,description,startDate,endDate,budget,org_name):
        from app import mail
        existing_campaign = Campaign.query.filter_by(campaignName=campaignName).first()
        url = f"https://www.msaadafund.com/campaigns/{existing_campaign.id}" #update once deployed 
        subject = f"{campaignName.upper()} by {org_name.upper()}"
        html_body = f"""
            <p>Hello {user}!. </p>
            <p>{org_name} is thrilled to announce the launch their latest campaign.</p>
            <p><strong>Campaign Name:</strong> {campaignName}</p>
            <p><strong>Description:</strong> {description}</p>
            <p><strong>Your target amount is Ksh:</strong> {budget}</p>
            <p><strong>Start Date:</strong> {startDate}</p>
            <p><strong>End Date:</strong> {endDate}</p>
            <p><strong>Campaign link:</strong> <a href="{url}">{url}</a></p>
            <p>Together, we can achieve meaningful impact and create positive change in our community!</p>
        """

        msg = Message(subject, recipients=[email])
        msg.html = html_body
        mail.send(msg)

    # been selected to be a signatory
    def send_signatory_email(email, name,organisation):
        from app import mail        
        subject = f"Signatory Selection by {organisation}"
        body = f"Dear {name},\n\nYou have been selected as a signatory on MsaadaFund Platform By {organisation}.\n\nBest regards,\nMsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    def send_signatory_email_removal(email, name, organisation):
        from app import mail
        subject = f"Signatory Removal from {organisation}"
        body = f"Dear {name},\n\nYou have been removed as a signatory from MsaadaFund Platform By {organisation}.\n\nBest regards,\nMsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_signatory_add(name,organisation,email):
        from app import mail
        subject = f"Signatory Added by {organisation}"
        body = f"Dear {organisation},\n\nYou have successfully added {name} as your signatory on MsaadaFund Platform.\n\nBest regards,\nMsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_approval_message(name,email,organisation,amount,trans_type,trans_account):
        from app import mail
        url = "https://www.msaadafund.com/user/login"  #change after hosting
        subject = f"Approval Request for {trans_type} by {organisation}"
        body = f"Dear {name},\n\nYou have been requested to approve a {trans_type} request of Ksh {amount} to {trans_account} by {organisation}.\n Please login to approve the request {url}.\n\n\nBest regards,\nMsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # Send mail after a transaction has been approved by all signatories
    def org_approval_message(org, trans):
        from app import mail
        subject = f"Transaction Approved"
        body = f"Dear {org.orgName},\nYour transaction: \n\nID: {trans.id} \n Type: {trans.trans_type} \n Amount: {trans.amount}\n Campaign: {trans.campaign_name}\nAccount: {trans.transaction_account_no} \n has been approved.\n\nBest regards,\n MsaadaFund Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # Send mail after a transaction has been rejected by signatories
    def org_rejected_message(org, trans):
        from app import mail
        subject = f"{trans.trans_type} transaction Rejected"
        body = f"Dear {org.orgName},\nYour transaction: \n\nID: {trans.id} \nType: {trans.trans_type} \nAmount: {trans.amount}\nCampaign: {trans.campaign_name}\nAccount: {trans.transaction_account_no} \n has been rejected.\n\nBest regards,\n MsaadaFund Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    # Send sign up account
    def send_user_signup_account(email, providers, accountNumber, orgName):
        from app import mail
        subject = f"{providers} Account Created Successful"
        body = f"Dear {orgName},\n\n Thank you for registering your {providers} account with account number {accountNumber} on our MsaadaFund Platform.\n\n Best regards,\n MsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    # send mail on success send money hook
    def send_mail_on_send_money_success(email, amount, transType, orgName):
        from app import mail
        subject = f"Transacation Successful"
        body = f"Dear {orgName},\n\n You transaction of Ksh {amount} to {transType} on our MsaadaFund Platform was successiful.\n\n Best regards,\n MsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_mail_on_send_money_failure (email, amount, transType, orgName):
        from app import mail
        subject = f"Transacation Failed"
        body = f"Dear {orgName},\n\n Your transaction of Ksh {amount} for {transType} on our MsaadaFund Platform was not successiful.Please try again\n\n Best regards,\n MsaadaFund Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)


# Generate otp
class  OTPGenerator():
    def send_otp(email, otp):
        from app import mail
        msg = Message('Password Reset OTP', recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)

    def send_pin_otp(email, otp):
        from app import mail
        msg = Message('Pin Reset OTP', recipients=[email])
        msg.body = f'Your OTP is: {otp}'
        mail.send(msg)

    def send_account_otp(email, otp):
        from app import mail
        msg = Message('Account Creation request OTP', recipients=[email])
        msg.body = f'Your OTP is: {otp}.\n\n<b>Disclaimer</b>: <i>Please do not share this OTP with anyone. It is confidential and should be used solely for account verification purposes.\nIf you believe you did not authorize this OTP creation, Please contact management to discuss the way forward.</i> '
        msg.html = msg.body
        mail.send(msg)

    def generate_otp():
        otp = ''.join(random.choices(string.digits, k=6))
        return otp
    
