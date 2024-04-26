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
        subject = "Donation successiful"
        body = f"Dear {name},\n\n Thank you for donating to {campaign} campaign on {date}.\nYour contribution is highly appreciated as it is used to make an impact in our community\n Best regards,\n {organisation}"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    #Send mail if the donation was not successiful
    def send_mail_donation_not_successiful(amount,date,name,campaign,email,organisation):
        from app import mail
        subject = "Donation failed"
        body = f"Dear {name},\n\n Thank you for donating to {campaign} campaign on {date}.\nUnfortunately your contribution was not successiful. Please try again\n Best regards,\n {organisation}"
        recipients = [email]
        mail.send_message(subject=subject, recipients=recipients, body=body)

    #Send mail after withdrawal has completed successifully
    def send_mail_on_successiful_withdrawal(amount, date, name, campaign, email, organisation):
        from app import mail
        subject = "Withdrawal successiful"
        body = f"Dear {name},\n\n Thank you for withdrawing from {campaign} campaign on {date}.\nYour withdrawal is highly appreciated as it is used to make an impact in our community\n Best regards,\n {organisation}"
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
        subject = "Campaign Created Successfully"
        body = f"Hello {organisation.orgName}! You have successfully created a campaign.\n\n" \
            f"Campaign Name: {campaignName}\n" \
            f"Description: {description}\n" \
            f"Category: {category}.\n" \
            f"Your target amount is Ksh: {targetAmount} \n" \
            f"Start Date: {startDate}\n" \
            f"End Date: {endDate} \n\n" \
            f"Good luck  with your campaign!"

        mail.send_message(subject=subject, recipients=[organisation.orgEmail], body=body)
    
    #Function to send verification to organisation
    def send_org_verification_mail(org):
        from app import mail
        subject = "Welcome to Msaada Mashinani"
        body = f"Dear {org.orgName},\n\n Thank you for registering on our Msaada Mashinani Platform.\nYour account is not verified. Please reply to this email for verification\n Best regards,\n Msaada Mashinani Team"
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
    
class Send_acc():    
    def send_user_signup_account(email, providers, accountNumber, orgName):
        from app import mail
        subject = "Account Creation"
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