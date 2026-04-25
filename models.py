from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Unit(db.Model):
    __tablename__ = 'units'
    id = db.Column(db.Integer, primary_key=True)
    unit_number = db.Column(db.String(20), unique=True, nullable=False)
    unit_type = db.Column(db.String(50), default='Studio')
    monthly_rent = db.Column(db.Float, nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tenants = db.relationship('Tenant', backref='unit', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'unit_number': self.unit_number,
            'unit_type': self.unit_type,
            'monthly_rent': self.monthly_rent,
            'is_occupied': self.is_occupied
        }

class Tenant(db.Model):
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(100))
    account_number = db.Column(db.String(20), unique=True, nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'))
    lease_start = db.Column(db.Date, nullable=False)
    lease_end = db.Column(db.Date, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    payments = db.relationship('Payment', backref='tenant', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'account_number': self.account_number,
            'unit_id': self.unit_id,
            'unit_number': self.unit.unit_number if self.unit else None,
            'monthly_rent': self.unit.monthly_rent if self.unit else 0,
            'lease_start': self.lease_start.isoformat(),
            'lease_end': self.lease_end.isoformat(),
            'is_active': self.is_active
        }

class Payment(db.Model):
    __tablename__ = 'payments'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'))
    amount = db.Column(db.Float, nullable=False)
    paybill_number = db.Column(db.String(20), nullable=False, default='505368')
    account_number = db.Column(db.String(20), nullable=False)
    transaction_code = db.Column(db.String(50))
    payment_date = db.Column(db.Date, default=date.today)
    month_paid_for = db.Column(db.String(7))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'tenant_id': self.tenant_id,
            'tenant_name': self.tenant.full_name if self.tenant else '',
            'amount': self.amount,
            'paybill_number': self.paybill_number,
            'account_number': self.account_number,
            'transaction_code': self.transaction_code,
            'payment_date': self.payment_date.isoformat(),
            'month_paid_for': self.month_paid_for,
            'notes': self.notes
        }
