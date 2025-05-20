# RequestHub - IT Support and Equipment Management System

RequestHub is a web-based system for managing IT maintenance and equipment requests at Columban College. The system allows students to submit IT support tickets and equipment borrowing requests, while administrators can manage and track these requests efficiently.

## Features

- User Authentication (Student and Admin roles)
- IT Support Ticket Management
- Equipment Borrowing System
- Real-time Request Status Updates
- Admin Dashboard with Equipment and User Management
- CSRF Protection for Enhanced Security
- Responsive Bootstrap 5 UI

## Default Admin Account
```
Email: admin@columban.edu
Username:admin
Password: admin12345
```

## Prerequisites

- Python 3.8 or higher
- MySQL (XAMPP)
- Modern web browser with JavaScript enabled

## Setup Instructions

1. Clone the repository:
```bash
git clone <repository-url>
cd requesthub
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Set up the MySQL database:
   - Start XAMPP and ensure MySQL service is running
   - Create a new database named 'requesthub'
   - The default database configuration uses:
     - Host: localhost
     - User: root
     - Password: (empty)
     - Database: requesthub

5. Initialize the database and create admin account:
```bash
flask db upgrade
flask shell
>>> from app import db
>>> from models.user import User
>>> from extensions import bcrypt
>>> admin = User(
...     username='admin',
...     email='admin@columban.edu',
...     password=bcrypt.generate_password_hash('admin12345').decode('utf-8'),
...     role='admin'
... )
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

## Running the Application

1. Start the Flask development server:
```bash
python app.py
```

The application will be available at `http://localhost:5000`

## System Features

### User Management
- Role-based access control (Admin/Student)
- User activation/deactivation
- Secure password handling
- User profile management

### Equipment Management
- Add, edit, and delete equipment
- Track equipment quantity and availability
- Categorize equipment (Computer, Audio/Visual, Photography, etc.)
- Equipment request workflow
- Real-time availability updates

### Request Management
- Equipment borrowing requests
- IT support tickets
- Request status tracking (Pending, Approved, Rejected, Returned)
- Email notifications (if configured)

### Admin Dashboard
- Overview of system statistics
- Manage equipment inventory
- Process equipment requests
- Handle user accounts
- View and manage support tickets

### Security Features
- CSRF protection
- Secure password hashing
- Role-based access control
- Input validation and sanitization
- Session management

## Recent Updates

1. Enhanced Security
   - Added CSRF protection
   - Improved form validation
   - Better error handling

2. User Management
   - Added user activation/deactivation
   - Improved user deletion with proper cascade
   - Better handling of user-related records

3. Equipment Management
   - Added equipment categories
   - Improved quantity tracking
   - Enhanced request workflow

4. UI Improvements
   - Bootstrap 5 integration
   - Responsive design
   - Better error notifications
   - Improved modal dialogs

## API Endpoints

### Authentication
- POST /auth/login - Login user
- POST /auth/register - Register new user
- GET /auth/logout - Logout user
- GET /auth/profile - View user profile

### Admin Routes
- GET /admin/dashboard - Admin dashboard
- GET /admin/users - Manage users
- GET /admin/equipment - Manage equipment
- GET /admin/requests - Manage requests

### Equipment Routes
- GET /equipment - List available equipment
- POST /equipment/request - Request equipment
- GET /equipment/requests - View user's requests

### Support Routes
- GET /support - Support dashboard
- POST /support/ticket - Create support ticket
- GET /support/tickets - View tickets

## Contributing

1. Fork the repository
2. Create a new branch for your feature
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License. 