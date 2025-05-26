from flask import Flask, jsonify, request, render_template, send_from_directory
from datetime import datetime
import os
from dotenv import load_dotenv
import logging
from .extensions import db, migrate
from .models import Transaction
from .mpesa import MpesaGateway
from flask_cors import CORS


load_dotenv()

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        db.create_all()
    
    return app

app = create_app()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize M-Pesa Gateway
mpesa = MpesaGateway(
    consumer_key=os.getenv('MPESA_CONSUMER_KEY'),
    consumer_secret=os.getenv('MPESA_CONSUMER_SECRET'),
    shortcode=os.getenv('MPESA_SHORTCODE'),
    passkey=os.getenv('MPESA_PASSKEY'),
    environment=os.getenv('MPESA_ENVIRONMENT', 'sandbox'),
    callback_url=os.getenv('MPESA_CALLBACK_URL')
)

@app.route('/api/stk-push', methods=['POST'])
def stk_push():
    try:
        data = request.get_json()
        required_fields = ['phone', 'amount', 'account_ref']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400

        response = mpesa.stk_push(
            phone=data['phone'],
            amount=data['amount'],
            account_ref=data['account_ref'],
            description=data.get('description', 'Payment')
        )

        # Save transaction
        transaction = Transaction(
            amount=data['amount'],
            phone=data['phone'],
            account_ref=data['account_ref'],
            description=data.get('description'),
            status='pending',
            checkout_request_id=response.get('CheckoutRequestID'),
            merchant_request_id=response.get('MerchantRequestID')
        )
        db.session.add(transaction)
        db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"STK Push Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/query-payment', methods=['POST'])
def query_payment():
    try:
        data = request.get_json()
        if 'checkout_id' not in data:
            return jsonify({'error': 'Missing checkout_id'}), 400

        transaction = Transaction.query.filter_by(
            checkout_request_id=data['checkout_id']
        ).first()

        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404

        response = mpesa.query_stk_status(transaction.checkout_request_id)
        
        # Update transaction status
        transaction.status = 'completed' if response.get('ResultCode') == '0' else 'failed'
        if 'MpesaReceiptNumber' in response:
            transaction.mpesa_receipt = response['MpesaReceiptNumber']
        if 'TransactionDate' in response:
            transaction.transaction_date = datetime.strptime(
                response['TransactionDate'], '%Y%m%d%H%M%S'
            )
        db.session.commit()

        return jsonify(response), 200

    except Exception as e:
        logger.error(f"Query Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    try:
        transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()
        return jsonify([t.to_dict() for t in transactions]), 200
    except Exception as e:
        logger.error(f"Transactions Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/mpesa-callback', methods=['POST'])
def mpesa_callback():
    try:
        data = request.get_json()
        callback = data.get('Body', {}).get('stkCallback', {})
        checkout_id = callback.get('CheckoutRequestID')
        
        transaction = Transaction.query.filter_by(checkout_request_id=checkout_id).first()
        if transaction:
            result_code = callback.get('ResultCode', 1)
            transaction.status = 'completed' if result_code == 0 else 'failed'
            db.session.commit()

        return jsonify({'ResultCode': 0, 'ResultDesc': 'Success'})
    
    except Exception as e:
        logger.error(f"Callback Error: {str(e)}")
        return jsonify({'ResultCode': 1, 'ResultDesc': str(e)})
    
# Serve Frontend
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_frontend(path):
    if path and os.path.exists(os.path.join(app.template_folder, path)):
        return send_from_directory(app.template_folder, path)
    return render_template('index.html')



