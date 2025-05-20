from extensions import db
from datetime import datetime

class MaintenanceRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, in_progress, completed, cancelled
    category = db.Column(db.String(50), nullable=False)  # hardware, software, network, other
    equipment_type = db.Column(db.String(50))  # computer, printer, network_device, etc.
    asset_tag = db.Column(db.String(50))  # Asset tag or serial number
    software_name = db.Column(db.String(100))  # For software-related issues
    error_message = db.Column(db.Text)  # Any error messages encountered
    troubleshooting_done = db.Column(db.Text)  # Steps already taken
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Relationships are already defined in User model

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'location': self.location,
            'priority': self.priority,
            'status': self.status,
            'category': self.category,
            'equipment_type': self.equipment_type,
            'asset_tag': self.asset_tag,
            'software_name': self.software_name,
            'error_message': self.error_message,
            'troubleshooting_done': self.troubleshooting_done,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'user': {
                'id': self.user.id,
                'username': self.user.username,
                'email': self.user.email
            },
            'assigned_to': {
                'id': self.assignee.id,
                'username': self.assignee.username,
                'email': self.assignee.email
            } if self.assignee else None
        } 