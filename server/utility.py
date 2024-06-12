#helper function

#function to check wallet balance
import random
import string
from flask_mail import Message
from flask import jsonify, url_for, render_template
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
        url = f"http://localhost:3000/campaign/{existing_campaign.id}" #update once deployed 
        subject = f"{campaignName.upper()} Created Successfully"
        body = f"Hello {organisation.orgName}!\n\nYou have successfully created a campaign.\n\n" \
            f"Campaign Name: {campaignName}\n\n" \
            f"Description: {description}\n\n" \
            f"Category: {category}.\n" \
            f"Your target amount is Ksh: {targetAmount} \n" \
            f"Start Date: {startDate}\n" \
            f"End Date: {endDate} \n" \
            f"Campaign link: {url} \n\n" \
            f"Good luck  with your campaign!"

        mail.send_message(subject=subject, recipients=[organisation.orgEmail], body=body)
    
    #Function to send verification to organisation
    def send_org_verification_mail(org):
        from app import mail
        subject = "Welcome to Msaada Mashinani"
        body = f"Dear {org.orgName},\n\n Thank you for registering on our Msaada Mashinani Platform.\nYour account is not verified. Please reply to this email for verification\n\n Best regards,\n Msaada Mashinani Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    #Org registration mail
    def send_registration_email(org_email, org_name):
        from app import mail
        subject = "Organization Registration Confirmation"
        body = f"Hello: {org_name},\n\nThank you for registering on our Msaada Mashinani Platform.\n\nRegards,\n Msaada Mashinani Team"
        
        try:
            mail.send_message(subject=subject, recipients=[org_email], body=body)
            return True
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    #Function to send users email after sign up
    def send_user_signup_mail(user):
        from app import mail
        subject = "Welcome to Msaada Mashinani"
        body = f"Dear {user.firstName} {user.lastName},\n\n Thank you for registering on our Msaada Mashinani Platform.\n\n Best regards,\n Msaada Mashinani Team"
        recipients = [user.email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # send subscriptions
    def send_subscription_email(email,user,org_name):
        from app import mail
        subject = f"Subscription to {org_name.upper()}"
        body = f"Dear {user},\n\nWe're excited to inform you that you've successfully subscribed to receive updates on {org_name.upper()} latest campaigns and initiatives.\n\nYou're now part of our community dedicated to making a positive impact..\n\nBest regards,\nMsaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_subscribers_createCampaign(email,user,campaignName,description,startDate,endDate,budget,org_name):
        from app import mail
        existing_campaign = Campaign.query.filter_by(campaignName=campaignName).first()
        url = f"http://localhost:3000/campaign/{existing_campaign.id}" #update once deployed 
        subject = f"{campaignName.upper()} by {org_name.upper()}"
        body = f"Dear {user},\n\nWe're thrilled to announce the launch of our latest campaign,{campaignName.upper()}. This initiative represents our continued commitment to our cause.\n\n Here's a brief overview of the campaign: \n Title:{campaignName}\n Description:{description}\n Start Date: {startDate}\n End Date: {endDate}\n Budget:{budget}\n Campaign link:{url}\n\nYou're now part of our community dedicated to making a positive impact.\n\nWe invite you to join us in making a difference by supporting this campaign. Whether it's spreading the word, volunteering your time, or contributing in any way you can, your participation is invaluable.\n\nStay tuned for updates as the campaign progresses. Together, we can achieve meaningful impact and create positive change in our community.\n\n Best regards,\n Msaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # been selected to be a signatory
    def send_signatory_email(email, name,organisation):
        from app import mail        
        subject = f"Signatory Selection by {organisation}"
        body = f"Dear {name},\n\nYou have been selected to be a signatory on Msaada Mashinani Platform By {organisation}.\n\nBest regards,\nMsaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    def send_signatory_email_removal(email, name, organisation):
        from app import mail
        subject = f"Signatory Removal from {organisation}"
        body = f"Dear {name},\n\nYou have been removed as a signatory from Msaada Mashinani Platform By {organisation}.\n\nBest regards,\nMsaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_signatory_add(name,organisation,email):
        from app import mail
        subject = f"Signatory Added by {organisation}"
        body = f"Dear {organisation},\n\nYou have  added {name} as your signatory on Msaada Mashinani Platform.\n\nBest regards,\nMsaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    def send_approval_message(name,email,organisation,amount,trans_type,trans_account):
        from app import mail
        url = "http://localhost:3000/user/login"  #change after hosting
        subject = f"Approval Request for {trans_type} by {organisation}"
        body = f"Dear {name},\n\nYou have been requested to approve a {trans_type} request of Ksh {amount} to {trans_account} by {organisation}.\n Please login to approve the request {url}.\n\n\nBest regards,\nMsaada Mashinani Team"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # Send mail after a transaction has been approved by all signatories
    def org_approval_message(org, trans):
        from app import mail
        subject = f"Transaction Approved"
        body = f"Dear {org.orgName},\nYour transaction: \n\nID: {trans.id} \n Type: {trans.trans_type} \n Amount: {trans.amount}\n Campaign: {trans.campaign_name}\nAccount: {trans.transaction_account_no} \n has been approved.\n\nBest regards,\n Msaada Mashinani Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    # Send mail after a transaction has been rejected by signatories
    def org_rejected_message(org, trans):
        from app import mail
        subject = f"{trans.trans_type} transaction Rejected"
        body = f"Dear {org.orgName},\nYour transaction: \n\nID: {trans.id} \nType: {trans.trans_type} \nAmount: {trans.amount}\nCampaign: {trans.campaign_name}\nAccount: {trans.transaction_account_no} \n has been rejected.\n\nBest regards,\n Msaada Mashinani Team"
        recipients = [org.orgEmail]
        mail.send_message(subject=subject, recipients=recipients, body=body)
    
    # Send sign up account
    def send_user_signup_account(email, providers, accountNumber, orgName):
        from app import mail
        subject = f"{providers} Account Created Successful"
        body = f"Dear {orgName},\n\n Thank you for registering your {providers} account with account number {accountNumber} on our Msaada Mashinani Platform.\n\n Best regards,\n Msaada Mashinani Team"
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
    
