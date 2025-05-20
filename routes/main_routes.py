from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_login import current_user, login_required, login_user, logout_user
from models.user import User
from extensions import db, bcrypt
from models.equipment import Equipment
from models.equipment_request import EquipmentRequest
from datetime import datetime, timedelta
from sqlalchemy import and_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('main.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@main_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('main.login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
    
    return render_template('auth/register.html')

@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get current date
    now = datetime.now()
    
    # Get active requests (pending or approved)
    active_requests = EquipmentRequest.query.filter(
        EquipmentRequest.user_id == current_user.id,
        EquipmentRequest.status.in_(['pending', 'approved']),
        EquipmentRequest.end_date >= now
    ).count()
    
    # Get approved requests
    approved_requests = EquipmentRequest.query.filter(
        EquipmentRequest.user_id == current_user.id,
        EquipmentRequest.status == 'approved'
    ).count()
    
    # Get currently borrowed equipment
    borrowed_equipment = EquipmentRequest.query.filter(
        EquipmentRequest.user_id == current_user.id,
        EquipmentRequest.status == 'approved',
        EquipmentRequest.start_date <= now,
        EquipmentRequest.end_date >= now
    ).count()
    
    # Get pending returns (approved requests that are due within 7 days)
    pending_returns = EquipmentRequest.query.filter(
        EquipmentRequest.user_id == current_user.id,
        EquipmentRequest.status == 'approved',
        EquipmentRequest.end_date >= now,
        EquipmentRequest.end_date <= now + timedelta(days=7)
    ).count()
    
    # Get recent equipment requests
    recent_requests = EquipmentRequest.query.filter_by(user_id=current_user.id)\
        .order_by(EquipmentRequest.created_at.desc())\
        .limit(5)\
        .all()
    
    # Get available equipment
    available_equipment = Equipment.query.filter(
        Equipment.status == 'available',
        Equipment.available_quantity > 0
    ).all()
    
    # Get upcoming returns
    upcoming_returns = EquipmentRequest.query.filter(
        EquipmentRequest.user_id == current_user.id,
        EquipmentRequest.status == 'approved',
        EquipmentRequest.end_date >= now
    ).order_by(EquipmentRequest.end_date.asc())\
     .limit(5)\
     .all()
    
    return render_template('dashboard.html',
                         active_requests=active_requests,
                         approved_requests=approved_requests,
                         borrowed_equipment=borrowed_equipment,
                         pending_returns=pending_returns,
                         recent_requests=recent_requests,
                         available_equipment=available_equipment,
                         upcoming_returns=upcoming_returns,
                         now=now)

@main_bp.route('/requests/create')
@login_required
def create_request():
    return render_template('requests/create.html', current_user=current_user) 