from app import create_app
from models.user import User
from extensions import db, bcrypt

def update_admin_password():
    try:
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            # Update existing admin's password
            admin.password = bcrypt.generate_password_hash('admin12345').decode('utf-8')
            db.session.commit()
            print("Admin password updated successfully!")
            print("Email: admin@columban.edu")
            print("Password: admin12345")
        else:
            # Create new admin user
            hashed_password = bcrypt.generate_password_hash('admin12345').decode('utf-8')
            admin = User(
                username='admin',
                email='admin@columban.edu',
                password=hashed_password,
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Admin user created successfully!")
            print("Email: admin@columban.edu")
            print("Password: admin12345")
            
    except Exception as e:
        db.session.rollback()
        print(f"Error updating admin user: {str(e)}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        update_admin_password() 