from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from models.maintenance_request import MaintenanceRequest
from models.user import User
from extensions import db
from functools import wraps
from datetime import datetime

maintenance_bp = Blueprint('maintenance', __name__)

@maintenance_bp.route('/maintenance/request/new', methods=['GET', 'POST'])
@login_required
def create_request():
    if request.method == 'POST':
        try:
            # Create new request with base fields
            new_request = MaintenanceRequest(
                title=request.form['title'],
                description=request.form['description'],
                location=request.form['location'],
                priority=request.form['priority'],
                category=request.form['category'],
                user_id=current_user.id
            )
            
            # Add category-specific fields
            if request.form['category'] == 'hardware':
                new_request.equipment_type = request.form.get('equipment_type')
                new_request.asset_tag = request.form.get('asset_tag')
            elif request.form['category'] == 'software':
                new_request.software_name = request.form.get('software_name')
                new_request.error_message = request.form.get('error_message')
            
            # Add troubleshooting steps if provided
            new_request.troubleshooting_done = request.form.get('troubleshooting_done')
            
            db.session.add(new_request)
            db.session.commit()
            
            flash('IT support request submitted successfully!', 'success')
            return redirect(url_for('maintenance.list_requests'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting request: ' + str(e), 'error')
    
    return render_template('maintenance/request.html')

@maintenance_bp.route('/maintenance/requests')
@login_required
def list_requests():
    if current_user.role == 'admin':
        requests = MaintenanceRequest.query.order_by(MaintenanceRequest.created_at.desc()).all()
        admins = User.query.filter_by(role='admin').all()
    else:
        requests = MaintenanceRequest.query.filter_by(user_id=current_user.id)\
                                        .order_by(MaintenanceRequest.created_at.desc()).all()
        admins = None
    
    return render_template('maintenance/list.html', requests=requests, admins=admins)

@maintenance_bp.route('/maintenance/request/<int:request_id>')
@login_required
def get_request(request_id):
    request = MaintenanceRequest.query.get_or_404(request_id)
    
    # Check if user has permission to view this request
    if current_user.role != 'admin' and request.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify(request.to_dict())

@maintenance_bp.route('/maintenance/request/<int:request_id>', methods=['PUT'])
@login_required
def update_request(request_id):
    request_item = MaintenanceRequest.query.get_or_404(request_id)
    
    # Check if user has permission to edit this request
    if current_user.role != 'admin' and request_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # If request is completed, only admin can edit
    if request_item.status == 'completed' and current_user.role != 'admin':
        return jsonify({'error': 'Cannot edit completed request'}), 403
    
    data = request.get_json()
    
    try:
        # Regular users can only update these fields
        if current_user.role != 'admin':
            allowed_fields = ['title', 'description', 'location', 'priority']
            for field in allowed_fields:
                if field in data:
                    setattr(request_item, field, data[field])
        else:
            # Admins can update all fields
            for field in ['title', 'description', 'location', 'priority', 'status', 'assigned_to']:
                if field in data:
                    setattr(request_item, field, data[field])
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Request updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@maintenance_bp.route('/maintenance/request/<int:request_id>/cancel', methods=['POST'])
@login_required
def cancel_request(request_id):
    request_item = MaintenanceRequest.query.get_or_404(request_id)
    
    # Check if user has permission to cancel this request
    if current_user.role != 'admin' and request_item.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # Cannot cancel completed requests
    if request_item.status == 'completed':
        return jsonify({'error': 'Cannot cancel completed request'}), 403
    
    try:
        request_item.status = 'cancelled'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Request cancelled successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@maintenance_bp.route('/maintenance/request/<int:request_id>/accept', methods=['POST'])
@login_required
def accept_request(request_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    request_item = MaintenanceRequest.query.get_or_404(request_id)
    
    try:
        request_item.status = 'in_progress'
        request_item.assigned_to = current_user.id
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Request accepted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@maintenance_bp.route('/maintenance/request/<int:request_id>/complete', methods=['POST'])
@login_required
def complete_request(request_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    request_item = MaintenanceRequest.query.get_or_404(request_id)
    
    try:
        request_item.status = 'completed'
        request_item.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Request marked as completed'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@maintenance_bp.route('/maintenance/request/<int:request_id>/delete', methods=['DELETE'])
@login_required
def delete_request(request_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    request_item = MaintenanceRequest.query.get_or_404(request_id)
    
    try:
        db.session.delete(request_item)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Request deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Template filters for status and priority colors
@maintenance_bp.app_template_filter('status_color')
def status_color(status):
    colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'completed': 'success',
        'cancelled': 'danger'
    }
    return colors.get(status, 'secondary')

@maintenance_bp.app_template_filter('priority_color')
def priority_color(priority):
    colors = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'urgent': 'danger'
    }
    return colors.get(priority, 'secondary')

@maintenance_bp.app_template_filter('format_status')
def format_status(status):
    return status.replace('_', ' ').title()
