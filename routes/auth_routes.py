from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from extensions import db, bcrypt
from models.user import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_login import login_user, logout_user, login_required, current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            if request.is_json:
                return jsonify({'message': 'Email already registered'}), 400
            flash('Email already registered', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=data['username']).first():
            if request.is_json:
                return jsonify({'message': 'Username already taken'}), 400
            flash('Username already taken', 'error')
            return render_template('auth/register.html')

        # Hash password
        hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')

        # Create new user (only allow student role through registration)
        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            role='student'  # Force student role for registration
        )

        db.session.add(new_user)
        db.session.commit()

        if request.is_json:
            return jsonify({'message': 'User registered successfully'}), 201
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form

        # Get the identifier (email or username) and password
        identifier = data.get('email')  # The form field is named 'email' but can contain username too
        password = data.get('password')

        if not identifier or not password:
            flash('Please provide both identifier and password', 'error')
            return render_template('auth/login.html')

        # Try to find user by email first
        user = User.query.filter_by(email=identifier).first()
        if not user:
            # If not found by email, try username
            user = User.query.filter_by(username=identifier).first()

        if user and bcrypt.check_password_hash(user.password, password):
            # Check if user is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact an administrator.', 'error')
                return render_template('auth/login.html')
                
            login_user(user)
            next_page = request.args.get('next')
            
            if next_page:
                # Ensure the next_page is a relative URL to prevent open redirect
                if not next_page.startswith('/'):
                    next_page = None
            
            if user.role == 'admin':
                return redirect(next_page or url_for('admin.dashboard'))
            else:
                return redirect(next_page or url_for('main.dashboard'))

        flash('Invalid email/username or password', 'error')
        return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    if request.method == 'GET':
        if request.is_json:
            return jsonify(current_user.to_dict()), 200
        return render_template('auth/profile.html')
    
    elif request.method == 'PUT':
        if not request.is_json:
            return jsonify({'success': False, 'message': 'Content-Type must be application/json'}), 400
        
        data = request.get_json()
        
        # Update allowed fields
        if 'email' in data:
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'success': False, 'message': 'Email already taken'}), 400
            current_user.email = data['email']
            
        if 'username' in data:
            existing_user = User.query.filter_by(username=data['username']).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'success': False, 'message': 'Username already taken'}), 400
            current_user.username = data['username']
            
        if 'password' in data and data['password']:
            current_user.password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
            
        try:
            db.session.commit()
            return jsonify({'success': True, 'message': 'Profile updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': str(e)}), 500

@auth_bp.route('/reactivate-admin')
def reactivate_admin():
    admin = User.ensure_admin_exists()
    if admin and admin.is_active:
        flash('Admin account has been created/reactivated.', 'success')
    else:
        flash('Could not create/reactivate admin account.', 'error')
    return redirect(url_for('auth.login'))

@auth_bp.route('/activate-all')
def activate_all():
    User.activate_all_users()
    flash('All user accounts have been activated.', 'success')
    return redirect(url_for('auth.login')) 