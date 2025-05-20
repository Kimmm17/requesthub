-- Drop database if exists and create new one
DROP DATABASE IF EXISTS requesthub;
CREATE DATABASE requesthub;
USE requesthub;

-- Create users table
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'student',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create equipment table
CREATE TABLE equipment (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'available',
    quantity INT NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Create request table (for IT support requests)
CREATE TABLE request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    category VARCHAR(50) NOT NULL,
    user_id INT NOT NULL,
    assigned_to INT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (assigned_to) REFERENCES user(id)
);

-- Create equipment_request table
CREATE TABLE equipment_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    equipment_id INT NOT NULL,
    user_id INT NOT NULL,
    start_date DATETIME NOT NULL,
    end_date DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    purpose TEXT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (equipment_id) REFERENCES equipment(id),
    FOREIGN KEY (user_id) REFERENCES user(id)
);

-- Insert default admin user
INSERT INTO user (username, email, password, role) VALUES 
('admin', 'admin@columban.edu.ph', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdsBHrpxFPH.Xt2', 'admin');

-- Insert default equipment
INSERT INTO equipment (name, description, category, status, quantity) VALUES
('Dell Latitude Laptop', 'Intel Core i5, 8GB RAM, 256GB SSD', 'laptop', 'available', 5),
('HP ProBook Laptop', 'Intel Core i7, 16GB RAM, 512GB SSD', 'laptop', 'available', 3),
('Epson Projector EB-X05', '3,300 lumens, XGA resolution', 'projector', 'available', 2),
('ViewSonic PA503S Projector', '3,800 lumens, SVGA resolution', 'projector', 'available', 2),
('ASUS Laptop X515', 'Intel Core i3, 4GB RAM, 1TB HDD', 'laptop', 'available', 4); 