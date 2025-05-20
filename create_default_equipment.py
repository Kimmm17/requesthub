from app import create_app
from extensions import db
from models.equipment import Equipment

def create_default_equipment():
    app = create_app()
    
    with app.app_context():
        # Default equipment list
        equipment_list = [
            {
                'name': 'Dell Latitude Laptop',
                'description': 'Intel Core i5, 8GB RAM, 256GB SSD',
                'category': 'laptop',
                'quantity': 5,
                'status': 'available'
            },
            {
                'name': 'HP ProBook Laptop',
                'description': 'Intel Core i7, 16GB RAM, 512GB SSD',
                'category': 'laptop',
                'quantity': 3,
                'status': 'available'
            },
            {
                'name': 'Epson Projector EB-X05',
                'description': '3,300 lumens, XGA resolution',
                'category': 'projector',
                'quantity': 2,
                'status': 'available'
            },
            {
                'name': 'ViewSonic PA503S Projector',
                'description': '3,800 lumens, SVGA resolution',
                'category': 'projector',
                'quantity': 2,
                'status': 'available'
            },
            {
                'name': 'ASUS Laptop X515',
                'description': 'Intel Core i3, 4GB RAM, 1TB HDD',
                'category': 'laptop',
                'quantity': 4,
                'status': 'available'
            }
        ]
        
        # Add equipment if they don't exist
        for eq_data in equipment_list:
            if not Equipment.query.filter_by(name=eq_data['name']).first():
                equipment = Equipment(**eq_data)
                db.session.add(equipment)
                print(f"Added {eq_data['name']}")
        
        try:
            db.session.commit()
            print("Default equipment added successfully!")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding equipment: {str(e)}")

if __name__ == '__main__':
    create_default_equipment() 