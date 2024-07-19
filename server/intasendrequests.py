# to handle transactions from ntasend
from flask import jsonify,make_response
import os
from intasend import APIService
import requests
from models import db
from dotenv import load_dotenv
load_dotenv()


token=os.getenv("INTA_SEND_API_KEY")
publishable_key= os.getenv('PUBLISHABLE_KEY')
main_pocket= os.getenv('MAIN_WALLET')
service = APIService(token=token,publishable_key=publishable_key, test=False)


def buy_airtime(wallet_id,transaction,org_name):
    try:        
        url = "https://api.intasend.com/api/v1/send-money/initiate/"

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
    
    except Exception as e:
        return make_response(jsonify({"error":str(e)}), 400)


# pay bill function
def pay_to_paybill(wallet_id,transaction):
    try:
        transactions= [{
                        'name':transaction.name , 
                        'account':transaction.transaction_account_no, 
                        'account_type':'PayBill', 
                        'account_reference':transaction.acc_refence, 
                        'amount':float(transaction.amount), 
                        'narrative':transaction.narrative
                        }]
        response = service.transfer.mpesa_b2b(wallet_id=wallet_id, currency='KES', transactions=transactions)
        if response.get("error"):
            error_message = response.get("error")[0]
            return  make_response(jsonify({'error':error_message}),400)
        
        #approve transaction
        approved_response = service.transfer.approve(response)

        if approved_response.get("error"):
            transaction.trans_status = 'Failed'
            error_message = approved_response.get("error")[0].get("detail")
            transaction.batch_status = error_message
        else:
            transaction.tracking_id = approved_response.get('tracking_id')
            transaction.batch_status = approved_response.get('status')
            transaction.trans_status = approved_response.get('transactions')[0].get('status')
            transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

        db.session.commit()
        return make_response(jsonify(approved_response), 200)
    
    except Exception as e:
        return make_response(jsonify({"error":str(e)}), 400)

# till number function
def pay_to_till(wallet_id, transaction):
    try:
        transactions= [{
                'name':transaction.name ,
                'account':int(transaction.transaction_account_no),
                'account_type':'TillNumber',
                'amount':float(transaction.amount),
                'narrative':transaction.narrative
                }]
        response = service.transfer.mpesa_b2b(wallet_id=wallet_id, currency='KES', transactions=transactions)
        if response.get("error"):
            error_message = response.get("error")[0]
            return  make_response(jsonify({'error':error_message}),400)
        
        #approve transaction
        approved_response = service.transfer.approve(response)

        if approved_response.get("error"):
            transaction.trans_status = 'Failed'
            error_message = approved_response.get("error")[0].get("detail")
            transaction.batch_status = error_message
        else:
            transaction.tracking_id = approved_response.get('tracking_id')
            transaction.batch_status = approved_response.get('status')
            transaction.trans_status = approved_response.get('transactions')[0].get('status')
            transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

        db.session.commit()
        return make_response(jsonify(approved_response), 200)
    
    except Exception as e:
        print(e)
        return jsonify({"error":str(e)}),500

# withdraw to bank function
def withdraw_to_bank(wallet_id,transaction):
    try:
        url = "https://api.intasend.com/api/v1/send-money/initiate/"

        payload = {
            "currency": "KES",
            "provider": "PESALINK",
            "wallet_id": wallet_id,
            "transactions": [
                {
                    "account": transaction.transaction_account_no,
                    "amount": transaction.amount,
                    "bank_code": transaction.bank_code,
                    "narrative": "Withdrawal Money"
                }
            ]
        }
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": "Bearer " + token
        }

        response = requests.post(url, json=payload, headers=headers)
        intersend_data=response.json()
        # print(intersend_data)
        if intersend_data.get("errors"):
            error_message = intersend_data.get("errors")[0].get("detail")
            return  make_response(jsonify({'error':error_message}),400)
        approved_response = service.transfer.approve(intersend_data)

        if approved_response.get("error"):
            transaction.trans_status = 'Failed'
            error_message = approved_response.get("error")[0].get("detail")
            transaction.batch_status = error_message
        else:
            transaction.tracking_id = approved_response.get('tracking_id')
            transaction.batch_status = approved_response.get('status')
            transaction.trans_status = approved_response.get('transactions')[0].get('status')
            transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

        db.session.commit()
        return make_response(jsonify(approved_response), 200)

    except Exception as e:
        return jsonify({"error":str(e)}),500

# withdraw to mpesa function
def withdraw_to_mpesa(wallet_id, transaction):
    try:
        transactions = [{'name': transaction.name, 'account': transaction.transaction_account_no, 'amount': float(transaction.amount)}]

        response = service.transfer.mpesa(wallet_id=wallet_id, currency='KES', transactions=transactions)
        if response.get('error'):
            error_message = response.get("error")[0].get("detail")
            return jsonify({'error':error_message})
        
        approved_response = service.transfer.approve(response)

        if approved_response.get("error"):
            transaction.trans_status = 'Failed'
            error_message = approved_response.get("error")[0].get("detail")
            transaction.batch_status = error_message
        else:
            transaction.tracking_id = approved_response.get('tracking_id')
            transaction.batch_status = approved_response.get('status')
            transaction.trans_status = approved_response.get('transactions')[0].get('status')
            transaction.request_ref_id = approved_response.get('transactions')[0].get('request_reference_id')

        db.session.commit()
        return make_response(jsonify(approved_response), 200)
    
    except Exception as e:
        return jsonify({"error":str(e)}),500

