from extensions import db
from datetime import datetime

class SupportTicket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # hardware, software, network, other
    priority = db.Column(db.String(20), nullable=False)  # low, medium, high, urgent
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    location = db.Column(db.String(100), nullable=False)  # Building and room number
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    resolution = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'status': self.status,
            'location': self.location,
            'assigned_to': self.assigned_to,
            'resolution': self.resolution,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        } 