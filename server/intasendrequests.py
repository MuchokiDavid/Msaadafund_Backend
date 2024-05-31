# to handle transactions from ntasend
from flask import jsonify,make_response
import os
from intasend import APIService
import requests
from models import db



token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
main_pocket= os.getenv('MAIN_WALLET')
service = APIService(token=token,publishable_key=publishable_key, test=True)


def buy_airtime(wallet_id,transaction,org_name):
    url = "https://sandbox.intasend.com/api/v1/send-money/initiate/"

    payload = {
        "currency": "KES",
        "provider": "AIRTIME",
        "wallet_id": wallet_id,
        "transactions": [
            {
                "name": org_name,
                "account": transaction.transaction_account_no,
                "amount": transaction.amount,
                "category_name": "Airtime",
                "narrative": "Airtime purchase"
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + token
    }

    response = requests.post(url, json=payload, headers=headers)
    approved_response = response.json()

    if approved_response.get("errors"):
        transaction.trans_status = 'Failed'
        error_message = approved_response.get("errors")[0].get("detail")
        transaction.batch_status = error_message
    else:
        approved_response = service.transfer.approve(approved_response)
        transaction.tracking_id = approved_response.get('tracking_id')
        transaction.batch_status = approved_response.get('status')
        transaction.trans_status = approved_response.get('transactions')[0].get('status')
        transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

    db.session.commit()
    return make_response(jsonify(approved_response), 200)


# pay bill route

def pay_to_paybill(wallet_id,transaction):
    print(transactions)
    transactions= [{
                    'name':transaction.name , 
                    'account':transaction.account, 
                    'account_type':'PayBill', 
                    'account_reference':transaction.account_reference, 
                    'amount':float(transaction.amount), 
                    'narrative':transaction.narrative
                    }]
    response = service.transfer.mpesa_b2b(wallet_id=wallet_id, currency='KES', transactions=transactions)
    print(wallet_id)
    if response.get("errors"):
        error_message = response.get("errors")[0].get("detail")
        return  make_response(jsonify({'error':error_message}),400)
    
    #approve transaction
    approved_response = service.transfer.approve(response)

    if approved_response.get("errors"):
        transaction.trans_status = 'Failed'
        error_message = approved_response.get("errors")[0].get("detail")
        transaction.batch_status = error_message
    else:
        approved_response = service.transfer.approve(approved_response)
        transaction.tracking_id = approved_response.get('tracking_id')
        transaction.batch_status = approved_response.get('status')
        transaction.trans_status = approved_response.get('transactions')[0].get('status')
        transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

    db.session.commit()
    return make_response(jsonify(approved_response), 200)


def withdraw_to_bank():
    pass

def pay_to_till():
    pass

def withdraw_to_mpesa():
    pass

