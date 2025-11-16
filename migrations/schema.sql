-- FoodLink Connect Database Schema
-- MySQL 5.7+ or MariaDB 10.2+

-- Create database
CREATE DATABASE IF NOT EXISTS foodlink_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE foodlink_db;

-- Users table (All system users: Admin, Volunteer, Client)
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    role ENUM('admin', 'volunteer', 'client') NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Clients table (Extended information for registered families)
CREATE TABLE IF NOT EXISTS clients (
    client_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    client_number VARCHAR(50) UNIQUE,
    address TEXT NOT NULL,
    family_size INT NOT NULL,
    allergies TEXT,
    food_preferences TEXT,
    income_proof_path VARCHAR(500),
    verification_status ENUM('pending', 'verified', 'rejected') DEFAULT 'pending',
    verified_date DATETIME,
    verified_by INT,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (verified_by) REFERENCES users(user_id),
    INDEX idx_client_number (client_number),
    INDEX idx_verification_status (verification_status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Donations table (Food rescue/pickup records)
CREATE TABLE IF NOT EXISTS donations (
    donation_id INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id INT NOT NULL,
    donation_date DATETIME NOT NULL,
    weight_kg DECIMAL(10, 2) NOT NULL,
    food_type VARCHAR(100),
    source VARCHAR(255),
    description TEXT,
    status ENUM('collected', 'in_storage', 'distributed') DEFAULT 'collected',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (volunteer_id) REFERENCES users(user_id),
    INDEX idx_volunteer (volunteer_id),
    INDEX idx_date (donation_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Food inventory table (Current food stock)
CREATE TABLE IF NOT EXISTS food_inventory (
    inventory_id INT AUTO_INCREMENT PRIMARY KEY,
    food_category VARCHAR(100) NOT NULL,
    quantity_kg DECIMAL(10, 2) NOT NULL,
    expiry_date DATE,
    source VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_category (food_category),
    INDEX idx_expiry (expiry_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Distribution records (Food given to clients)
CREATE TABLE IF NOT EXISTS distributions (
    distribution_id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    volunteer_id INT NOT NULL,
    distribution_date DATETIME NOT NULL,
    weight_kg DECIMAL(10, 2) NOT NULL,
    items_description TEXT,
    client_signature BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (volunteer_id) REFERENCES users(user_id),
    INDEX idx_client (client_id),
    INDEX idx_date (distribution_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Volunteer schedules (Shift management)
CREATE TABLE IF NOT EXISTS volunteer_schedules (
    schedule_id INT AUTO_INCREMENT PRIMARY KEY,
    volunteer_id INT NOT NULL,
    schedule_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    status ENUM('scheduled', 'completed', 'cancelled') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (volunteer_id) REFERENCES users(user_id),
    INDEX idx_volunteer_date (volunteer_id, schedule_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Activity logs (Audit trail)
CREATE TABLE IF NOT EXISTS activity_logs (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(255) NOT NULL,
    entity_type VARCHAR(100),
    entity_id INT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    INDEX idx_user_date (user_id, created_at),
    INDEX idx_entity (entity_type, entity_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Insert default admin user (Password: Admin@123)
-- Password hash for "Admin@123" using SHA-256
INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
VALUES ('admin@foodlink.com', 
        'e86f78a8a3caf0b60d8e74e5942aa6d86dc150cd3c03338aef25b7d2d7e3acc7', 
        'System Administrator', 
        '1234567890', 
        'admin', 
        TRUE)
ON DUPLICATE KEY UPDATE email=email;

-- Sample volunteer user (Password: Volunteer@123)
-- Password hash for "Volunteer@123" using SHA-256
INSERT INTO users (email, password_hash, full_name, phone, role, is_active)
VALUES ('volunteer@foodlink.com', 
        '3e789d2f398b50e9999d157196a68254dc44c67a04b9adefcefe8c7a195e2c6d', 
        'Sample Volunteer', 
        '0987654321', 
        'volunteer', 
        TRUE)
ON DUPLICATE KEY UPDATE email=email;

-- Note: The password hashes above are examples. In production, use the hash_password() 
-- function from app.utils.security to generate proper password hashes.

-- pickup table 
CREATE TABLE IF NOT EXISTS pickups (
    pickup_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    inventory_id INT NOT NULL,
    quantity DECIMAL(10,2) NOT NULL,
    status ENUM('pending','approved','completed','rejected') DEFAULT 'pending',
    pickup_time DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (inventory_id) REFERENCES food_inventory(inventory_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

