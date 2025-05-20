from extensions import db
from datetime import datetime

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='available')  # available, out_of_stock
    quantity = db.Column(db.Integer, nullable=False, default=1)
    available_quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    requests = db.relationship('EquipmentRequest', backref='equipment', lazy=True)

    def __init__(self, *args, **kwargs):
        super(Equipment, self).__init__(*args, **kwargs)
        if 'available_quantity' not in kwargs:
            self.available_quantity = self.quantity

    @property
    def is_available(self):
        return self.available_quantity > 0

    def update_status(self):
        """Update equipment status based on available quantity"""
        self.status = 'available' if self.available_quantity > 0 else 'out_of_stock'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'quantity': self.quantity,
            'available_quantity': self.available_quantity,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 