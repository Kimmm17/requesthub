from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models.user import User
from models.equipment import Equipment
from models.equipment_request import EquipmentRequest
from models.request import Request
from models.support_ticket import SupportTicket
from models.maintenance_request import MaintenanceRequest
from extensions import db
from functools import wraps
from datetime import datetime
import traceback

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    # Get statistics for the dashboard
    pending_equipment_requests = EquipmentRequest.query.filter_by(status='pending').count()
    total_equipment = Equipment.query.count()
    total_users = User.query.count()
    pending_requests = SupportTicket.query.filter_by(status='pending').count()

    return render_template('admin/dashboard.html',
                         pending_equipment_requests=pending_equipment_requests,
                         total_equipment=total_equipment,
                         total_users=total_users,
                         pending_requests=pending_requests)

@admin_bp.route('/admin/users')
@login_required
@admin_required
def list_users():
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/admin/equipment')
@login_required
@admin_required
def manage_equipment():
    equipment = Equipment.query.all()
    return render_template('admin/equipment.html', equipment=equipment)

@admin_bp.route('/admin/equipment/add', methods=['POST'])
@login_required
@admin_required
def add_equipment():
    try:
        data = request.form

        if not data.get('name') or not data.get('category') or not data.get('quantity'):
            return jsonify({
                'success': False,
                'message': 'Missing required fields'
            }), 400

        new_equipment = Equipment(
            name=data['name'],
            description=data.get('description', ''),
            quantity=int(data['quantity']),
            available_quantity=int(data['quantity']),
            category=data.get('category', 'other'),
            status='available'
        )

        db.session.add(new_equipment)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Equipment added successfully!'
        })
    except ValueError as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': 'Invalid quantity value provided'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error adding equipment: {str(e)}'
        }), 500

@admin_bp.route('/admin/equipment/<int:equipment_id>', methods=['PUT'])
@login_required
@admin_required
def update_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    data = request.get_json()

    try:
        if 'name' in data:
            equipment.name = data['name']
        if 'description' in data:
            equipment.description = data['description']
        if 'total_quantity' in data:
            old_total = equipment.total_quantity
            new_total = int(data['total_quantity'])
            equipment.total_quantity = new_total
            equipment.available_quantity += (new_total - old_total)
        if 'category' in data:
            equipment.category = data['category']

        db.session.commit()
        return jsonify({'message': 'Equipment updated successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/equipment/<int:equipment_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_equipment(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    
    # Check if there are any pending requests
    if EquipmentRequest.query.filter_by(equipment_id=equipment_id, status='pending').first():
        return jsonify({'error': 'Cannot delete equipment with pending requests'}), 400

    try:
        db.session.delete(equipment)
        db.session.commit()
        return jsonify({'message': 'Equipment deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/requests')
@login_required
@admin_required
def manage_requests():
    requests = EquipmentRequest.query.order_by(EquipmentRequest.created_at.desc()).all()
    return render_template('admin/manage_requests.html', requests=requests)

@admin_bp.route('/admin/request/<int:request_id>/update', methods=['POST'])
@login_required
@admin_required
def update_request_status(request_id):
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({'success': False, 'message': 'Missing status'})

    equipment_request = EquipmentRequest.query.get_or_404(request_id)
    equipment = equipment_request.equipment

    try:
        if new_status == 'approved':
            if equipment.available_quantity >= equipment_request.quantity:
                equipment.available_quantity -= equipment_request.quantity
                equipment.update_status()  # Update equipment status
                equipment_request.status = 'approved'
                flash(f'Request #{request_id} has been approved.', 'success')
            else:
                return jsonify({
                    'success': False,
                    'message': 'Not enough equipment available'
                })
        elif new_status == 'rejected':
            equipment_request.status = 'rejected'
            flash(f'Request #{request_id} has been rejected.', 'success')
        elif new_status == 'returned':
            if equipment_request.status == 'approved':
                equipment.available_quantity += equipment_request.quantity
                equipment.update_status()  # Update equipment status
                equipment_request.status = 'returned'
                flash(f'Equipment has been marked as returned for request #{request_id}.', 'success')
            else:
                return jsonify({
                    'success': False,
                    'message': 'Can only return approved equipment'
                })

        db.session.commit()
        return jsonify({'success': True, 'message': f'Request status updated to {new_status}'})

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/admin/request/<int:request_id>/assign', methods=['POST'])
@login_required
@admin_required
def assign_request(request_id):
    maintenance_request = Request.query.get_or_404(request_id)
    data = request.get_json()
    
    try:
        maintenance_request.assigned_to = data['assigned_to']
        maintenance_request.status = 'assigned'
        maintenance_request.assigned_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'message': 'Request assigned successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/admin/users/<int:user_id>/details')
@login_required
@admin_required
def get_user_details(user_id):
    user = User.query.get_or_404(user_id)
    
    # Get user's equipment requests
    equipment_requests = EquipmentRequest.query.filter_by(user_id=user_id).all()
    equipment_request_data = [{
        'equipment_name': req.equipment.name,
        'request_date': req.created_at.strftime('%Y-%m-%d'),
        'quantity': req.quantity,
        'status': req.status
    } for req in equipment_requests]
    
    # Get user's support tickets
    submitted_tickets = SupportTicket.query.filter_by(user_id=user_id).all()
    support_ticket_data = [{
        'subject': ticket.title,
        'description': ticket.description,
        'created_date': ticket.created_at.strftime('%Y-%m-%d'),
        'status': ticket.status
    } for ticket in submitted_tickets]
    
    return jsonify({
        'equipment_requests': equipment_request_data,
        'support_tickets': support_ticket_data
    })

@admin_bp.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        return jsonify({
            'success': False,
            'message': 'Cannot modify admin user status'
        })
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'User {"activated" if user.is_active else "deactivated"} successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        })

@admin_bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    print(f"Starting delete process for user {user_id}")
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        print(f"Cannot delete admin user {user_id}")
        return jsonify({
            'success': False,
            'message': 'Cannot delete admin user'
        })
    
    try:
        print(f"Checking active requests for user {user_id}")
        # Check for active equipment requests
        active_equipment_requests = EquipmentRequest.query.filter(
            EquipmentRequest.user_id == user_id,
            EquipmentRequest.status.in_(['pending', 'approved'])
        ).first()
        
        if active_equipment_requests:
            print(f"User {user_id} has active equipment requests")
            return jsonify({
                'success': False,
                'message': 'Cannot delete user with pending or approved equipment requests. Please ensure all requests are completed or rejected first.'
            }), 400

        # Check for active support tickets
        active_tickets = SupportTicket.query.filter(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_(['open', 'in_progress'])
        ).first()

        if active_tickets:
            print(f"User {user_id} has active support tickets")
            return jsonify({
                'success': False,
                'message': 'Cannot delete user with open or in-progress support tickets.'
            }), 400

        print(f"All checks passed, proceeding to delete user {user_id}")
        
        # The cascade='all, delete-orphan' in the User model will handle deleting all related records
        db.session.delete(user)
        db.session.commit()
        
        print(f"Successfully deleted user {user_id}")
        return jsonify({
            'success': True,
            'message': 'User and associated records deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user {user_id}:")
        print(str(e))
        return jsonify({
            'success': False,
            'message': f'Error deleting user: {str(e)}'
        }), 500

@admin_bp.route('/admin/request/<int:request_id>/details')
@login_required
@admin_required
def get_request_details(request_id):
    equipment_request = EquipmentRequest.query.get_or_404(request_id)
    
    return jsonify({
        'equipment': {
            'name': equipment_request.equipment.name,
            'category': equipment_request.equipment.category,
            'available_quantity': equipment_request.equipment.available_quantity
        },
        'quantity': equipment_request.quantity,
        'purpose': equipment_request.purpose,
        'start_date': equipment_request.start_date.strftime('%Y-%m-%d'),
        'end_date': equipment_request.end_date.strftime('%Y-%m-%d'),
        'user': {
            'username': equipment_request.user.username,
            'email': equipment_request.user.email
        }
    }) 