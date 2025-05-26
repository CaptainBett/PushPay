from datetime import datetime
from .main import db

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    account_ref = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    checkout_request_id = db.Column(db.String(255))
    merchant_request_id = db.Column(db.String(255))
    mpesa_receipt = db.Column(db.String(255))
    transaction_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'amount': self.amount,
            'phone': self.phone,
            'account_ref': self.account_ref,
            'description': self.description,
            'status': self.status,
            'checkout_id': self.checkout_request_id,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'created_at': self.created_at.isoformat()
        }