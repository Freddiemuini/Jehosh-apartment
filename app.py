from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from models import db, Unit, Tenant, Payment
from datetime import datetime, date
from sqlalchemy import func

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///jehosh_apartment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
CORS(app)

db.init_app(app)

with app.app_context():
    db.create_all()
    if Unit.query.count() == 0:
        sample_units = [
            Unit(unit_number='A1', unit_type='Studio', monthly_rent=15000, is_occupied=False),
            Unit(unit_number='A2', unit_type='Studio', monthly_rent=15000, is_occupied=False),
            Unit(unit_number='B1', unit_type='1 Bedroom', monthly_rent=25000, is_occupied=False),
            Unit(unit_number='B2', unit_type='1 Bedroom', monthly_rent=25000, is_occupied=False),
            Unit(unit_number='C1', unit_type='2 Bedroom', monthly_rent=35000, is_occupied=False)
        ]
        db.session.add_all(sample_units)
        db.session.commit()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/units', methods=['GET'])
def get_units():
    units = Unit.query.all()
    return jsonify([u.to_dict() for u in units]), 200

@app.route('/api/units', methods=['POST'])
def add_unit():
    data = request.json
    unit = Unit(
        unit_number=data['unit_number'],
        unit_type=data.get('unit_type', 'Studio'),
        monthly_rent=data['monthly_rent']
    )
    db.session.add(unit)
    db.session.commit()
    return jsonify(unit.to_dict()), 201

@app.route('/api/units/<int:unit_id>', methods=['PUT'])
def update_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    data = request.json
    unit.unit_number = data.get('unit_number', unit.unit_number)
    unit.unit_type = data.get('unit_type', unit.unit_type)
    unit.monthly_rent = data.get('monthly_rent', unit.monthly_rent)
    db.session.commit()
    return jsonify(unit.to_dict()), 200

@app.route('/api/units/<int:unit_id>', methods=['DELETE'])
def delete_unit(unit_id):
    unit = Unit.query.get_or_404(unit_id)
    if unit.is_occupied:
        return jsonify({'error': 'Cannot delete occupied unit'}), 400
    db.session.delete(unit)
    db.session.commit()
    return jsonify({'message': 'Unit deleted'}), 200

@app.route('/api/tenants', methods=['GET'])
def get_tenants():
    tenants = Tenant.query.all()
    return jsonify([t.to_dict() for t in tenants]), 200

@app.route('/api/tenants', methods=['POST'])
def add_tenant():
    data = request.json
    account_number = data.get('account_number')
    if not account_number:
        last_tenant = Tenant.query.order_by(Tenant.id.desc()).first()
        next_id = (last_tenant.id + 1) if last_tenant else 1
        account_number = f'JOSH{next_id:04d}'
    tenant = Tenant(
        full_name=data['full_name'],
        phone=data['phone'],
        email=data.get('email'),
        account_number=account_number,
        unit_id=data['unit_id'],
        lease_start=datetime.strptime(data['lease_start'], '%Y-%m-%d').date(),
        lease_end=datetime.strptime(data['lease_end'], '%Y-%m-%d').date()
    )
    unit = Unit.query.get(data['unit_id'])
    if unit:
        unit.is_occupied = True
    db.session.add(tenant)
    db.session.commit()
    return jsonify(tenant.to_dict()), 201

@app.route('/api/tenants/<int:tenant_id>', methods=['PUT'])
def update_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    data = request.json
    old_unit_id = tenant.unit_id
    tenant.full_name = data.get('full_name', tenant.full_name)
    tenant.phone = data.get('phone', tenant.phone)
    tenant.email = data.get('email', tenant.email)
    if 'lease_start' in data:
        tenant.lease_start = datetime.strptime(data['lease_start'], '%Y-%m-%d').date()
    if 'lease_end' in data:
        tenant.lease_end = datetime.strptime(data['lease_end'], '%Y-%m-%d').date()
    if 'unit_id' in data and data['unit_id'] != tenant.unit_id:
        old_unit = Unit.query.get(old_unit_id)
        if old_unit:
            old_unit.is_occupied = False
        new_unit = Unit.query.get(data['unit_id'])
        if new_unit:
            new_unit.is_occupied = True
        tenant.unit_id = data['unit_id']
    db.session.commit()
    return jsonify(tenant.to_dict()), 200

@app.route('/api/tenants/<int:tenant_id>', methods=['DELETE'])
def delete_tenant(tenant_id):
    tenant = Tenant.query.get_or_404(tenant_id)
    unit = Unit.query.get(tenant.unit_id)
    if unit:
        unit.is_occupied = False
    db.session.delete(tenant)
    db.session.commit()
    return jsonify({'message': 'Tenant deleted'}), 200

@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = Payment.query.order_by(Payment.payment_date.desc()).all()
    return jsonify([p.to_dict() for p in payments]), 200

@app.route('/api/payments', methods=['POST'])
def add_payment():
    data = request.json
    if data.get('paybill_number') != '505368':
        return jsonify({'error': 'Invalid Paybill number. Must be 505368'}), 400
    tenant = Tenant.query.filter_by(account_number=data['account_number']).first()
    if not tenant:
        return jsonify({'error': 'Tenant with this account number not found'}), 404
    payment = Payment(
        tenant_id=tenant.id,
        amount=data['amount'],
        paybill_number=data['paybill_number'],
        account_number=data['account_number'],
        transaction_code=data.get('transaction_code'),
        month_paid_for=data.get('month_paid_for', datetime.now().strftime('%Y-%m')),
        notes=data.get('notes')
    )
    db.session.add(payment)
    db.session.commit()
    return jsonify(payment.to_dict()), 201

@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    total_units = Unit.query.count()
    occupied_units = Unit.query.filter_by(is_occupied=True).count()
    total_tenants = Tenant.query.filter_by(is_active=True).count()
    current_month = date.today().strftime('%Y-%m')
    monthly_collections = db.session.query(func.sum(Payment.amount)).filter(
        Payment.month_paid_for == current_month
    ).scalar() or 0
    tenants = Tenant.query.filter_by(is_active=True).all()
    total_expected = sum(t.unit.monthly_rent for t in tenants if t.unit)
    total_paid = db.session.query(func.sum(Payment.amount)).scalar() or 0
    outstanding = total_expected - total_paid
    recent_payments = Payment.query.order_by(Payment.payment_date.desc()).limit(5).all()
    return jsonify({
        'total_units': total_units,
        'occupied_units': occupied_units,
        'vacant_units': total_units - occupied_units,
        'occupancy_rate': round((occupied_units / total_units) * 100, 2) if total_units > 0 else 0,
        'total_tenants': total_tenants,
        'monthly_collections': float(monthly_collections),
        'outstanding_balance': float(outstanding),
        'recent_payments': [p.to_dict() for p in recent_payments]
    }), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)