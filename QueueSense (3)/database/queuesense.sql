-- ============================================
-- QueueSense Database Schema
-- Smart Queues. Human Care.
-- ============================================

-- Create the database if it doesn't exist
CREATE DATABASE IF NOT EXISTS queuesense;

-- Use the queuesense database
USE queuesense;

-- ============================================
-- DROP EXISTING TABLES (To ensure schema update)
-- ============================================
SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS queues;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS services;
SET FOREIGN_KEY_CHECKS = 1;

-- ============================================
-- TABLE 1: services
-- Purpose: Stores different service types
-- (Hospital, Bank, Government, Railway, etc.)
-- ============================================
CREATE TABLE IF NOT EXISTS services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,           -- Unique identifier for each service
    service_name VARCHAR(100) NOT NULL,                  -- Human-readable service name
    service_code VARCHAR(10) NOT NULL UNIQUE,            -- Short code for tokens (H, B, G, R)
    description TEXT,                                     -- Optional description of the service
    icon VARCHAR(50) DEFAULT 'fa-building',              -- Font Awesome icon class
    elder_weight INT DEFAULT 3,                          -- Priority weight for elderly users
    appointment_weight INT DEFAULT 2,                    -- Priority weight for appointment holders
    wait_time_weight INT DEFAULT 1,                      -- Priority weight per 10 min wait
    service_duration INT DEFAULT 20,                     -- Default service window in minutes
    is_active BOOLEAN DEFAULT TRUE,                      -- Whether service is currently active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Record creation timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP  -- Last update timestamp
);

-- ============================================
-- TABLE 2: locations
-- Purpose: Stores multiple locations per service
-- ============================================
CREATE TABLE IF NOT EXISTS locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,          -- Unique identifier for each location
    service_id INT NOT NULL,                             -- Foreign key to services table
    location_name VARCHAR(100) NOT NULL,                 -- Name of the location
    address VARCHAR(255),                                -- Physical address
    operating_hours_start TIME DEFAULT '09:00:00',       -- Opening time (default 9 AM)
    operating_hours_end TIME DEFAULT '17:00:00',         -- Closing time (default 5 PM)
    max_capacity INT DEFAULT 50,                         -- Maximum queue capacity
    is_active BOOLEAN DEFAULT TRUE,                      -- Whether location is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Record creation timestamp
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 3: users
-- Purpose: Stores registered users who join queues
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,              -- Unique user identifier
    username VARCHAR(50) NOT NULL UNIQUE,                -- Username for login
    password_hash VARCHAR(255) NOT NULL,                 -- Bcrypt hashed password
    name VARCHAR(100) NOT NULL,                          -- Display name
    phone VARCHAR(20),                                   -- Phone number for notifications
    age INT,                                             -- Age for elder priority detection
    category ENUM('normal', 'elder') DEFAULT 'normal',   -- User category (auto-set based on age)
    role ENUM('user', 'staff', 'admin') DEFAULT 'user',  -- User role for access control
    is_active BOOLEAN DEFAULT TRUE,                      -- Whether account is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Registration timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- TABLE 4: staff
-- Purpose: Staff members who manage queues
-- ============================================
CREATE TABLE IF NOT EXISTS staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,             -- Unique staff identifier
    user_id INT NOT NULL UNIQUE,                         -- Links to users table
    assigned_services JSON,                              -- JSON array of service_ids staff can manage
    counter_number INT,                                  -- Assigned counter/window number
    is_available BOOLEAN DEFAULT TRUE,                   -- Whether staff is currently available
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Record creation timestamp
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 5: appointments
-- Purpose: Stores booking records with time windows
-- ============================================
CREATE TABLE IF NOT EXISTS appointments (
    app_id INT AUTO_INCREMENT PRIMARY KEY,               -- Unique appointment identifier
    user_id INT NOT NULL,                                -- Links to users table
    service_id INT NOT NULL,                             -- Links to services table
    location_id INT NOT NULL,                            -- Links to locations table
    appointment_date DATE NOT NULL,                      -- Date of appointment
    time_window_start TIME NOT NULL,                     -- Start of service window
    time_window_end TIME NOT NULL,                       -- End of service window (20 min later)
    status ENUM('scheduled', 'checked_in', 'serving', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
    notes TEXT,                                          -- Optional notes or special requests
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Booking timestamp
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 6: queue_elder
-- Purpose: Priority queue for elderly users
-- ============================================
CREATE TABLE IF NOT EXISTS queue_elder (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,             -- Unique queue record identifier
    app_id INT,                                          -- Optional link to appointment
    user_id INT NOT NULL,                                -- Links to users table
    service_id INT NOT NULL,                             -- Links to services table
    location_id INT NOT NULL,                            -- Links to locations table
    token VARCHAR(20) NOT NULL,                          -- Queue token (e.g., H001)
    priority_score INT DEFAULT 0,                        -- Calculated priority score
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- When user joined queue
    called_time TIMESTAMP NULL,                          -- When token was called
    served_time TIMESTAMP NULL,                          -- When service completed
    served_flag BOOLEAN DEFAULT FALSE,                   -- Whether service is complete
    is_emergency BOOLEAN DEFAULT FALSE,                  -- Emergency queue flag
    counter_number INT,                                  -- Assigned counter when called
    status ENUM('waiting', 'called', 'serving', 'completed', 'no_show') DEFAULT 'waiting',
    FOREIGN KEY (app_id) REFERENCES appointments(app_id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 7: queue_normal
-- Purpose: FIFO queue for normal users
-- ============================================
CREATE TABLE IF NOT EXISTS queue_normal (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,             -- Unique queue record identifier
    app_id INT,                                          -- Optional link to appointment
    user_id INT NOT NULL,                                -- Links to users table
    service_id INT NOT NULL,                             -- Links to services table
    location_id INT NOT NULL,                            -- Links to locations table
    token VARCHAR(20) NOT NULL,                          -- Queue token (e.g., B042)
    priority_score INT DEFAULT 0,                        -- Calculated priority score
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,   -- When user joined queue
    called_time TIMESTAMP NULL,                          -- When token was called
    served_time TIMESTAMP NULL,                          -- When service completed
    served_flag BOOLEAN DEFAULT FALSE,                   -- Whether service is complete
    is_emergency BOOLEAN DEFAULT FALSE,                  -- Emergency queue flag
    counter_number INT,                                  -- Assigned counter when called
    status ENUM('waiting', 'called', 'serving', 'completed', 'no_show') DEFAULT 'waiting',
    FOREIGN KEY (app_id) REFERENCES appointments(app_id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE
);

-- ============================================
-- TABLE 8: analytics
-- Purpose: Aggregated metrics for reporting
-- ============================================
CREATE TABLE IF NOT EXISTS analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,         -- Unique analytics record
    service_id INT NOT NULL,                             -- Links to services table
    location_id INT NOT NULL,                            -- Links to locations table
    date DATE NOT NULL,                                  -- Date of analytics
    total_users_served INT DEFAULT 0,                    -- Total users served that day
    total_elder_served INT DEFAULT 0,                    -- Elder users served
    total_normal_served INT DEFAULT 0,                   -- Normal users served
    total_emergency INT DEFAULT 0,                       -- Emergency cases handled
    avg_wait_time_minutes DECIMAL(10,2) DEFAULT 0,       -- Average wait time in minutes
    avg_service_time_minutes DECIMAL(10,2) DEFAULT 0,    -- Average service duration
    peak_hour INT,                                       -- Hour with highest traffic (0-23)
    no_shows INT DEFAULT 0,                              -- Number of no-shows
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,      -- Record creation timestamp
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    UNIQUE KEY unique_daily_analytics (service_id, location_id, date)
);

-- ============================================
-- TABLE 9: system_settings
-- Purpose: Global system configuration
-- ============================================
CREATE TABLE IF NOT EXISTS system_settings (
    setting_id INT AUTO_INCREMENT PRIMARY KEY,           -- Unique setting identifier
    setting_key VARCHAR(50) NOT NULL UNIQUE,             -- Setting name
    setting_value TEXT,                                  -- Setting value
    description VARCHAR(255),                            -- Description of the setting
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- ============================================
-- INSERT DEFAULT DATA
-- ============================================

-- Insert default services (Hospital, Bank, Government, Railway)
INSERT INTO services (service_name, service_code, description, icon, elder_weight, appointment_weight, wait_time_weight, service_duration) VALUES
('Hospital', 'H', 'Healthcare and medical services', 'fa-hospital', 3, 2, 1, 20),
('Bank', 'B', 'Banking and financial services', 'fa-building-columns', 3, 2, 1, 15),
('Government', 'G', 'Government office services', 'fa-landmark', 3, 2, 1, 25),
('Railway', 'R', 'Railway station ticketing and services', 'fa-train', 3, 2, 1, 10);

-- Insert default locations for each service
INSERT INTO locations (service_id, location_name, address, operating_hours_start, operating_hours_end, max_capacity) VALUES
-- Hospital locations
(1, 'City General Hospital', '123 Medical Center Drive', '08:00:00', '20:00:00', 100),
(1, 'Downtown Health Clinic', '456 Main Street', '09:00:00', '18:00:00', 50),
-- Bank locations
(2, 'Central Bank - Main Branch', '789 Finance Avenue', '09:00:00', '17:00:00', 75),
(2, 'Central Bank - Mall Branch', '321 Shopping Plaza', '10:00:00', '21:00:00', 40),
-- Government locations
(3, 'Municipal Office - City Center', '555 Government Complex', '09:00:00', '17:00:00', 60),
(3, 'Regional Services Office', '777 Admin Building', '09:00:00', '16:00:00', 45),
-- Railway locations
(4, 'Central Railway Station', '100 Station Road', '06:00:00', '22:00:00', 150),
(4, 'Suburban Railway Terminal', '200 Suburb Lane', '07:00:00', '21:00:00', 80);

-- Insert default admin user (password: Admin@123)
INSERT INTO users (username, password_hash, name, phone, age, category, role) VALUES
('admin', '$2b$12$xC4u2Tl6aEb31t2xqxghL.Lb3ummkB2zkUwb5bIc9DMTyx5t2xwP.', 'System Administrator', '1234567890', 35, 'normal', 'admin');

-- Insert default staff user (password: Staff@123)
INSERT INTO users (username, password_hash, name, phone, age, category, role) VALUES
('staff', '$2b$12$vopPRMcFD4EvtMfxstg7N.fYC133GkC2L.YJKK43u60padenfbEiy', 'Queue Staff Member', '0987654321', 28, 'normal', 'staff');

-- Link staff user to staff table (can manage all services)
INSERT INTO staff (user_id, assigned_services, counter_number, is_available) VALUES
(2, '[1, 2, 3, 4]', 1, TRUE);

-- Insert demo users (password: Username@123, e.g. Johndoe@123)
INSERT INTO users (username, password_hash, name, phone, age, category, role) VALUES
('johndoe', '$2b$12$14zOBhkdSzrpIvC7a12sbOr9iD.YdFQsm4ifIq0aO/hubT1RBS6UO', 'John Doe', '5551234567', 45, 'normal', 'user'),
('maryelder', '$2b$12$HL4WT.0EcpHGycbnTL8.uuBuKSdx7laugGOZISfcWgV7rcPzV5qWK', 'Mary Elder', '5559876543', 72, 'elder', 'user'),
('bobsmith', '$2b$12$TdjpxKTKdrza4yvuHXVCa.TJJxsCGwAyZbaAKW4xRcvP9AOHZYFUq', 'Bob Smith', '5554567890', 32, 'normal', 'user'),
('gracesenior', '$2b$12$qTah6cvMBVfqCKaOvCQ2z.fxi3C6Fa2zPNjKCg4i41eQtvdVtk1xG', 'Grace Senior', '5557654321', 68, 'elder', 'user');

-- Insert system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('elder_age_threshold', '60', 'Age threshold to classify user as elder'),
('default_service_window', '20', 'Default service window duration in minutes'),
('queue_refresh_interval', '5000', 'Queue status refresh interval in milliseconds'),
('voice_enabled', 'true', 'Enable voice announcements for token calls'),
('voice_repeat_count', '2', 'Number of times to repeat voice announcement');

-- ============================================
-- END OF SCHEMA
-- ============================================
