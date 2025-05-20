from extensions import db, login_manager, bcrypt
from datetime import datetime
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # student, admin, staff
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    
    # Relationships
    # Requests created by this user
    requests = db.relationship('Request', 
                             foreign_keys='Request.user_id',
                             backref='requester',
                             lazy=True,
                             cascade='all, delete-orphan')
    
    # Requests assigned to this user
    assigned_requests = db.relationship('Request',
                                      foreign_keys='Request.assigned_to',
                                      backref='assignee',
                                      lazy=True,
                                      cascade='all, delete-orphan')
    
    # Equipment requests
    equipment_requests = db.relationship('EquipmentRequest', 
                                       backref='user', 
                                       lazy=True,
                                       cascade='all, delete-orphan')
    
    # Support tickets created by this user
    submitted_tickets = db.relationship('SupportTicket',
                                      foreign_keys='SupportTicket.user_id',
                                      backref=db.backref('creator', lazy=True),
                                      lazy=True,
                                      cascade='all, delete-orphan')
    
    # Support tickets assigned to this user
    assigned_tickets = db.relationship('SupportTicket',
                                     foreign_keys='SupportTicket.assigned_to',
                                     backref=db.backref('technician', lazy=True),
                                     lazy=True,
                                     cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

    def toggle_active(self):
        # Prevent deactivation of admin accounts
        if self.role == 'admin':
            return True
        self.is_active = not self.is_active
        db.session.commit()
        return self.is_active
    
    @staticmethod
    def ensure_admin_exists():
        """Ensure the admin account exists and is active"""
        admin = User.query.filter_by(email='admin@columban.edu').first()
        
        if not admin:
            # Create admin account if it doesn't exist
            admin = User(
                username='admin',
                email='admin@columban.edu',
                password=bcrypt.generate_password_hash('admin12345').decode('utf-8'),
                role='admin',
                is_active=True
            )
            db.session.add(admin)
        else:
            # Ensure admin is active and has admin role
            admin.is_active = True
            admin.role = 'admin'
        
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        return admin
    
    @staticmethod
    def reactivate_admin():
        """Reactivate the admin account if it was deactivated"""
        admin = User.ensure_admin_exists()
        return admin
    
    @staticmethod
    def activate_all_users():
        """Activate all user accounts"""
        try:
            User.query.update({User.is_active: True})
            db.session.commit()
        except:
            db.session.rollback() 