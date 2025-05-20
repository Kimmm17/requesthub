from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from extensions import db, csrf
from models.support_ticket import SupportTicket
from models.user import User
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps

support_bp = Blueprint('support', __name__)

def tech_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'technician']:
            flash('Access denied. Technical staff privileges required.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@support_bp.route('/support')
def support_home():
    return render_template('support/home.html')

@support_bp.route('/support/tickets', methods=['GET', 'POST'])
@login_required
def tickets():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category')
        priority = request.form.get('priority')
        location = request.form.get('location')

        ticket = SupportTicket(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category,
            priority=priority,
            location=location,
            status='open'
        )

        try:
            db.session.add(ticket)
            db.session.commit()
            flash('Support ticket submitted successfully!', 'success')
            return redirect(url_for('support.view_ticket', ticket_id=ticket.id))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while submitting your ticket.', 'error')
            return redirect(url_for('support.tickets'))

    # Get user's tickets or all tickets for staff
    if current_user.role in ['admin', 'technician']:
        tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
    else:
        tickets = SupportTicket.query.filter_by(user_id=current_user.id)\
            .order_by(SupportTicket.created_at.desc()).all()
    
    # Get technicians for assignment
    technicians = User.query.filter(User.role.in_(['admin', 'technician'])).all()
    
    return render_template('support/tickets.html', tickets=tickets, technicians=technicians)

@support_bp.route('/support/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Check if user has permission to view ticket
    if current_user.role not in ['admin', 'technician'] and ticket.creator.id != current_user.id:
        flash('Access denied.', 'error')
        return redirect(url_for('support.tickets'))
    
    # Get technicians for assignment
    technicians = User.query.filter(User.role.in_(['admin', 'technician'])).all()
    
    return render_template('support/view_ticket.html', ticket=ticket, technicians=technicians)

@support_bp.route('/support/ticket/<int:ticket_id>/update', methods=['POST'])
@login_required
@tech_required
def update_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    status = request.form.get('status')
    resolution = request.form.get('resolution')
    assigned_to = request.form.get('assigned_to')
    
    if status:
        ticket.status = status
        if status == 'resolved':
            ticket.resolved_at = datetime.utcnow()
    
    if resolution:
        ticket.resolution = resolution
    
    if assigned_to:
        ticket.assigned_to = assigned_to
    
    try:
        db.session.commit()
        flash('Ticket updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while updating the ticket.', 'error')
    
    return redirect(url_for('support.view_ticket', ticket_id=ticket_id))

@support_bp.route('/support/dashboard')
@login_required
@tech_required
def support_dashboard():
    open_tickets = SupportTicket.query.filter_by(status='open').count()
    in_progress = SupportTicket.query.filter_by(status='in_progress').count()
    resolved_today = SupportTicket.query.filter(
        SupportTicket.status == 'resolved',
        SupportTicket.resolved_at >= datetime.now().date()
    ).count()
    
    my_tickets = SupportTicket.query.filter_by(assigned_to=current_user.id)\
        .order_by(SupportTicket.created_at.desc()).limit(5).all()
    
    urgent_tickets = SupportTicket.query.filter_by(priority='urgent', status='open')\
        .order_by(SupportTicket.created_at.desc()).all()
    
    return render_template('support/dashboard.html',
                         open_tickets=open_tickets,
                         in_progress=in_progress,
                         resolved_today=resolved_today,
                         my_tickets=my_tickets,
                         urgent_tickets=urgent_tickets)

# API Endpoints
@support_bp.route('/api/support/tickets', methods=['GET'])
@login_required
@csrf.exempt
def get_tickets_api():
    if current_user.role in ['admin', 'technician']:
        tickets = SupportTicket.query.all()
    else:
        tickets = SupportTicket.query.filter_by(user_id=current_user.id).all()
    
    return jsonify([ticket.to_dict() for ticket in tickets]), 200

@support_bp.route('/api/support/ticket/<int:ticket_id>', methods=['GET'])
@login_required
@csrf.exempt
def get_ticket_api(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    if current_user.role not in ['admin', 'technician'] and ticket.creator.id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(ticket.to_dict()), 200

@support_bp.route('/api/support/ticket/<int:ticket_id>', methods=['PUT'])
@login_required
@tech_required
@csrf.exempt
def update_ticket_api(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    data = request.get_json()
    
    if 'status' in data:
        ticket.status = data['status']
        if data['status'] == 'resolved':
            ticket.resolved_at = datetime.utcnow()
    
    if 'resolution' in data:
        ticket.resolution = data['resolution']
    
    if 'assigned_to' in data:
        ticket.assigned_to = data['assigned_to']
    
    try:
        db.session.commit()
        return jsonify({'message': 'Ticket updated successfully', 'ticket': ticket.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@support_bp.route('/support/tickets')
@login_required
def list_tickets():
    if current_user.role == 'admin':
        tickets = SupportTicket.query.order_by(SupportTicket.created_at.desc()).all()
        admins = User.query.filter_by(role='admin').all()
    else:
        tickets = SupportTicket.query.filter_by(user_id=current_user.id)\
                                   .order_by(SupportTicket.created_at.desc()).all()
        admins = None
    
    return render_template('support/list.html', tickets=tickets, admins=admins)

@support_bp.route('/support/ticket/new', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        try:
            new_ticket = SupportTicket(
                subject=request.form['subject'],
                description=request.form['description'],
                priority=request.form['priority'],
                category=request.form['category'],
                user_id=current_user.id
            )
            
            db.session.add(new_ticket)
            db.session.commit()
            
            flash('Support ticket submitted successfully!', 'success')
            return redirect(url_for('support.list_tickets'))
        except Exception as e:
            db.session.rollback()
            flash('Error submitting ticket: ' + str(e), 'error')
    
    return render_template('support/create.html')

@support_bp.route('/support/ticket/<int:ticket_id>')
@login_required
def get_ticket(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Check if user has permission to view this ticket
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    return jsonify(ticket.to_dict())

@support_bp.route('/support/ticket/<int:ticket_id>/accept', methods=['POST'])
@login_required
def accept_ticket(ticket_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    try:
        ticket.status = 'in_progress'
        ticket.assigned_to = current_user.id
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ticket accepted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@support_bp.route('/support/ticket/<int:ticket_id>/complete', methods=['POST'])
@login_required
def complete_ticket(ticket_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    try:
        ticket.status = 'resolved'
        ticket.resolved_at = datetime.utcnow()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ticket marked as resolved'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@support_bp.route('/support/ticket/<int:ticket_id>/delete', methods=['DELETE'])
@login_required
def delete_ticket(ticket_id):
    # Check if user is admin
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403
        
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    try:
        db.session.delete(ticket)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ticket deleted successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@support_bp.route('/support/ticket/<int:ticket_id>', methods=['PUT'])
@login_required
def update_ticket_details(ticket_id):
    ticket = SupportTicket.query.get_or_404(ticket_id)
    
    # Check if user has permission to edit this ticket
    if current_user.role != 'admin' and ticket.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized access'}), 403
    
    # If ticket is resolved, only admin can edit
    if ticket.status == 'resolved' and current_user.role != 'admin':
        return jsonify({'error': 'Cannot edit resolved ticket'}), 403
    
    data = request.get_json()
    
    try:
        # Regular users can only update these fields
        if current_user.role != 'admin':
            allowed_fields = ['subject', 'description', 'priority', 'category']
            for field in allowed_fields:
                if field in data:
                    setattr(ticket, field, data[field])
        else:
            # Admins can update all fields
            for field in ['subject', 'description', 'priority', 'category', 'status', 'assigned_to']:
                if field in data:
                    setattr(ticket, field, data[field])
            
            # Update resolved_at if status is changed to resolved
            if data.get('status') == 'resolved':
                ticket.resolved_at = datetime.utcnow()
        
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Ticket updated successfully'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# Template filters for status and priority colors
@support_bp.app_template_filter('status_color')
def status_color(status):
    colors = {
        'pending': 'warning',
        'in_progress': 'info',
        'resolved': 'success',
        'cancelled': 'danger'
    }
    return colors.get(status, 'secondary')

@support_bp.app_template_filter('priority_color')
def priority_color(priority):
    colors = {
        'low': 'success',
        'medium': 'warning',
        'high': 'danger',
        'urgent': 'danger'
    }
    return colors.get(priority, 'secondary')

@support_bp.app_template_filter('format_status')
def format_status(status):
    return status.replace('_', ' ').title() 