import base64
import requests
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MpesaGateway:
    def __init__(self, consumer_key, consumer_secret, shortcode, passkey, environment, callback_url):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.shortcode = shortcode
        self.passkey = passkey
        self.environment = environment
        self.callback_url = callback_url
        self.base_url = 'https://sandbox.safaricom.co.ke' if environment == 'sandbox' else 'https://api.safaricom.co.ke'
        self.access_token = self.get_access_token()

    def get_access_token(self):
        try:
            auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            response = requests.get(
                f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials",
                headers={'Authorization': f'Basic {auth}'},
                timeout=10
            )
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            logger.error(f"Auth Error: {str(e)}")
            raise

    def stk_push(self, phone, amount, account_ref, description):
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "TransactionType": "CustomerPayBillOnline",
                "Amount": amount,
                "PartyA": self.format_phone(phone),
                "PartyB": self.shortcode,
                "PhoneNumber": self.format_phone(phone),
                "CallBackURL": self.callback_url,
                "AccountReference": account_ref,
                "TransactionDesc": description
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/mpesa/stkpush/v1/processrequest",
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"STK Push Error: {str(e)}")
            raise

    def query_stk_status(self, checkout_request_id):
        try:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            password = base64.b64encode(
                f"{self.shortcode}{self.passkey}{timestamp}".encode()
            ).decode()

            payload = {
                "BusinessShortCode": self.shortcode,
                "Password": password,
                "Timestamp": timestamp,
                "CheckoutRequestID": checkout_request_id
            }

            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/mpesa/stkpushquery/v1/query",
                json=payload,
                headers=headers,
                timeout=15
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Query Error: {str(e)}")
            raise

    @staticmethod
    def format_phone(phone):
        cleaned = ''.join(filter(str.isdigit, phone))
        if cleaned.startswith('0'):
            return f'254{cleaned[1:]}'
        if cleaned.startswith('7'):
            return f'254{cleaned}'
        return cleaned