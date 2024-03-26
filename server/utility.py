#helper function

#function to check wallet balance
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