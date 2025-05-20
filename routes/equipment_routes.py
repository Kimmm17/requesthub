from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from extensions import db
from models.equipment import Equipment
from models.equipment_request import EquipmentRequest
from models.user import User
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import and_

equipment_bp = Blueprint('equipment', __name__)

@equipment_bp.route('/equipment')
@login_required
def list_equipment():
    equipment = Equipment.query.all()
    return render_template('equipment/list.html', equipment=equipment)

@equipment_bp.route('/equipment/request', methods=['GET', 'POST'])
@login_required
def request_equipment():
    if request.method == 'POST':
        equipment_id = request.form.get('equipment_id')
        quantity = int(request.form.get('quantity', 1))
        start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        purpose = request.form.get('purpose')

        equipment = Equipment.query.get_or_404(equipment_id)
        
        # Check if enough quantity is available
        if equipment.available_quantity < quantity:
            flash('Not enough equipment available.', 'error')
            return redirect(url_for('equipment.list_equipment'))

        # Create equipment request
        equipment_request = EquipmentRequest(
            user_id=current_user.id,
            equipment_id=equipment_id,
            quantity=quantity,
            start_date=start_date,
            end_date=end_date,
            purpose=purpose,
            status='pending'
        )

        try:
            db.session.add(equipment_request)
            db.session.commit()
            flash('Equipment request submitted successfully!', 'success')
            return redirect(url_for('equipment.list_equipment'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your request.', 'error')
            return redirect(url_for('equipment.list_equipment'))

    equipment = Equipment.query.all()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('equipment/request.html', equipment=equipment, today=today)

@equipment_bp.route('/equipment/manage')
@login_required
def manage_equipment():
    if current_user.role != 'admin':
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.dashboard'))
    
    equipment = Equipment.query.all()
    return render_template('equipment/manage.html', equipment=equipment)

@equipment_bp.route('/equipment/requests')
@login_required
def list_requests():
    if current_user.role == 'admin':
        requests = EquipmentRequest.query.all()
    else:
        requests = EquipmentRequest.query.filter_by(user_id=current_user.id).all()
    return render_template('equipment/requests.html', requests=requests)

@equipment_bp.route('/equipment/request/<int:request_id>/approve', methods=['POST'])
@login_required
def approve_request(request_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    equipment_request = EquipmentRequest.query.get_or_404(request_id)
    equipment = Equipment.query.get(equipment_request.equipment_id)

    if equipment.available_quantity < equipment_request.quantity:
        return jsonify({'error': 'Not enough equipment available'}), 400

    try:
        equipment_request.status = 'approved'
        equipment_request.approved_at = datetime.utcnow()
        equipment_request.approved_by = current_user.id
        equipment.available_quantity -= equipment_request.quantity
        
        db.session.commit()
        return jsonify({'message': 'Request approved successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@equipment_bp.route('/equipment/request/<int:request_id>/reject', methods=['POST'])
@login_required
def reject_request(request_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    equipment_request = EquipmentRequest.query.get_or_404(request_id)
    
    try:
        equipment_request.status = 'rejected'
        equipment_request.rejected_at = datetime.utcnow()
        equipment_request.rejected_by = current_user.id
        
        db.session.commit()
        return jsonify({'message': 'Request rejected successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# API endpoints for equipment management
@equipment_bp.route('/api/equipment', methods=['POST'])
@jwt_required()
def create_equipment():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    data = request.get_json()
    new_equipment = Equipment(
        name=data['name'],
        description=data.get('description'),
        category=data['category'],
        quantity=data.get('quantity', 1),
        status='available'
    )
    
    db.session.add(new_equipment)
    db.session.commit()
    
    return jsonify(new_equipment.to_dict()), 201

@equipment_bp.route('/api/equipment')
@jwt_required()
def get_equipment():
    category = request.args.get('category')
    status = request.args.get('status', 'available')
    
    query = Equipment.query
    
    if category:
        query = query.filter_by(category=category)
    if status:
        query = query.filter_by(status=status)
    
    equipment = query.all()
    return jsonify([eq.to_dict() for eq in equipment]), 200

@equipment_bp.route('/api/equipment/<int:equipment_id>', methods=['PUT'])
@jwt_required()
def update_equipment_api(equipment_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Unauthorized'}), 403
    
    equipment = Equipment.query.get_or_404(equipment_id)
    data = request.get_json()
    
    equipment.name = data.get('name', equipment.name)
    equipment.description = data.get('description', equipment.description)
    equipment.category = data.get('category', equipment.category)
    equipment.status = data.get('status', equipment.status)
    equipment.quantity = data.get('quantity', equipment.quantity)
    
    db.session.commit()
    
    return jsonify(equipment.to_dict()), 200

@equipment_bp.route('/api/equipment/available')
@jwt_required()
def get_available_equipment():
    category = request.args.get('category')
    query = Equipment.query.filter(Equipment.quantity > 0, Equipment.status == 'available')
    
    if category:
        query = query.filter_by(category=category)
    
    equipment = query.all()
    return jsonify([eq.to_dict() for eq in equipment]), 200

@equipment_bp.route('/api/equipment/<int:equipment_id>')
@jwt_required()
def get_equipment_details(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Get current active requests for this equipment
    active_requests = EquipmentRequest.query.filter(
        and_(
            EquipmentRequest.equipment_id == equipment_id,
            EquipmentRequest.status.in_(['approved', 'pending']),
            EquipmentRequest.end_date >= datetime.now()
        )
    ).count()
    
    # Calculate available quantity
    available_quantity = max(0, equipment.quantity - active_requests)
    
    response = equipment.to_dict()
    response['available_quantity'] = available_quantity
    return jsonify(response), 200

@equipment_bp.route('/api/equipment/request', methods=['POST'])
@jwt_required()
def request_equipment_api():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    equipment = Equipment.query.get_or_404(data['equipment_id'])
    start_date = datetime.fromisoformat(data['start_date'])
    end_date = datetime.fromisoformat(data['end_date'])
    
    # Check if dates are valid
    if start_date >= end_date:
        return jsonify({'message': 'End date must be after start date'}), 400
    
    if start_date < datetime.now():
        return jsonify({'message': 'Start date cannot be in the past'}), 400
    
    # Check overlapping requests
    overlapping_requests = EquipmentRequest.query.filter(
        and_(
            EquipmentRequest.equipment_id == equipment.id,
            EquipmentRequest.status.in_(['approved', 'pending']),
            EquipmentRequest.start_date <= end_date,
            EquipmentRequest.end_date >= start_date
        )
    ).count()
    
    if overlapping_requests >= equipment.quantity:
        return jsonify({
            'message': f'No {equipment.name} units available for the selected dates. Please choose different dates.'
        }), 400
    
    # Create the request
    new_request = EquipmentRequest(
        equipment_id=equipment.id,
        user_id=current_user_id,
        start_date=start_date,
        end_date=end_date,
        purpose=data['purpose'],
        status='pending'
    )
    
    db.session.add(new_request)
    db.session.commit()
    
    return jsonify({
        'message': 'Equipment request submitted successfully',
        'request': new_request.to_dict()
    }), 201

@equipment_bp.route('/api/equipment/request/<int:request_id>/status', methods=['PUT'])
@jwt_required()
def update_request_status(request_id):
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        return jsonify({'message': 'Unauthorized. Admin access required.'}), 403
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['approved', 'rejected', 'returned']:
        return jsonify({'message': 'Invalid status'}), 400
    
    eq_request = EquipmentRequest.query.get_or_404(request_id)
    equipment = Equipment.query.get(eq_request.equipment_id)
    
    if new_status == 'approved':
        # Check if equipment is still available
        overlapping_requests = EquipmentRequest.query.filter(
            and_(
                EquipmentRequest.equipment_id == equipment.id,
                EquipmentRequest.status == 'approved',
                EquipmentRequest.id != request_id,
                EquipmentRequest.start_date <= eq_request.end_date,
                EquipmentRequest.end_date >= eq_request.start_date
            )
        ).count()
        
        if overlapping_requests >= equipment.quantity:
            return jsonify({'message': 'No units available for the requested dates'}), 400
        
        # Update equipment status if all units are now in use
        if overlapping_requests + 1 >= equipment.quantity:
            equipment.status = 'in_use'
    
    elif new_status == 'returned':
        # Check if we can mark equipment as available
        active_requests = EquipmentRequest.query.filter(
            and_(
                EquipmentRequest.equipment_id == equipment.id,
                EquipmentRequest.status == 'approved',
                EquipmentRequest.id != request_id,
                EquipmentRequest.end_date >= datetime.now()
            )
        ).count()
        
        if active_requests < equipment.quantity:
            equipment.status = 'available'
    
    eq_request.status = new_status
    db.session.commit()
    
    return jsonify({
        'message': f'Request {new_status} successfully',
        'request': eq_request.to_dict()
    }), 200

@equipment_bp.route('/api/equipment/requests')
@jwt_required()
def get_all_requests():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if user.role != 'admin':
        # For regular users, only show their own requests
        requests = EquipmentRequest.query.filter_by(user_id=current_user_id).all()
    else:
        # For admins, show all requests with optional filters
        status = request.args.get('status')
        equipment_id = request.args.get('equipment_id')
        
        query = EquipmentRequest.query
        
        if status:
            query = query.filter_by(status=status)
        if equipment_id:
            query = query.filter_by(equipment_id=equipment_id)
            
        requests = query.all()
    
    return jsonify([req.to_dict() for req in requests]), 200 