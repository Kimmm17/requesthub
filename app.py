from flask import Flask, render_template, jsonify, request
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from extensions import db, bcrypt, migrate, csrf, login_manager
from routes.auth_routes import auth_bp
from routes.main_routes import main_bp
from routes.equipment_routes import equipment_bp
from routes.admin_routes import admin_bp
from routes.support_routes import support_bp
from routes.maintenance_routes import maintenance_bp
from models.user import User
from models.equipment import Equipment
from models.equipment_request import EquipmentRequest
from models.support_ticket import SupportTicket
from flask_wtf.csrf import CSRFError
import os

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_key_change_this_in_production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'mysql://root:@localhost/requesthub')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'jwt_dev_key_change_this_in_production')
    app.config['WTF_CSRF_ENABLED'] = True
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    migrate.init_app(app, db)  # Initialize Flask-Migrate
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Register error handlers
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.is_json:
            return jsonify({'error': 'CSRF token missing or invalid'}), 400
        return render_template('auth/login.html', csrf_error=True), 400
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(maintenance_bp)
    
    # Create database tables and ensure admin exists
    with app.app_context():
        db.create_all()
        User.ensure_admin_exists()
        User.activate_all_users()  # Activate all existing users
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True) 