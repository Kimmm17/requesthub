from app import app, db
from models.equipment import Equipment

def add_sample_equipment():
    equipment_list = [
        {
            'name': 'Projector',
            'description': 'HD Projector with HDMI and VGA inputs',
            'category': 'Audio/Visual',
            'status': 'available',
            'quantity': 5,
            'available_quantity': 5
        },
        {
            'name': 'Laptop',
            'description': 'Dell Latitude with Windows 10, 8GB RAM, 256GB SSD',
            'category': 'Computer',
            'status': 'available',
            'quantity': 10,
            'available_quantity': 10
        },
        {
            'name': 'Digital Camera',
            'description': 'Canon EOS with 18-55mm lens, includes SD card',
            'category': 'Photography',
            'status': 'available',
            'quantity': 3,
            'available_quantity': 3
        },
        {
            'name': 'Microphone Set',
            'description': 'Wireless microphone set with receiver and two handheld mics',
            'category': 'Audio/Visual',
            'status': 'available',
            'quantity': 4,
            'available_quantity': 4
        },
        {
            'name': 'Printer',
            'description': 'HP LaserJet Color Printer with network capability',
            'category': 'Office',
            'status': 'available',
            'quantity': 2,
            'available_quantity': 2
        }
    ]

    for equipment_data in equipment_list:
        equipment = Equipment(**equipment_data)
        db.session.add(equipment)
    
    try:
        db.session.commit()
        print("Sample equipment added successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error adding equipment: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        add_sample_equipment() 