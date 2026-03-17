-- =============================================
-- QueueSense Database Schema
-- MySQL Database Setup
-- =============================================

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS queuesense;
USE queuesense;

-- =============================================
-- Drop existing tables (for clean setup)
-- =============================================
DROP TABLE IF EXISTS analytics;
DROP TABLE IF EXISTS queue_normal;
DROP TABLE IF EXISTS queue_elder;
DROP TABLE IF EXISTS appointments;
DROP TABLE IF EXISTS staff_services;
DROP TABLE IF EXISTS staff;
DROP TABLE IF EXISTS locations;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS users;

-- =============================================
-- Users Table
-- Stores all system users (customers, staff, admin)
-- =============================================
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    age INT,
    category ENUM('normal', 'elder') DEFAULT 'normal',
    role ENUM('user', 'staff', 'admin') DEFAULT 'user',
    status ENUM('active', 'inactive', 'blocked') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_category (category)
);

-- =============================================
-- Services Table
-- Stores all available services
-- =============================================
CREATE TABLE services (
    service_id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    service_code VARCHAR(10) UNIQUE NOT NULL,
    description TEXT,
    service_duration INT DEFAULT 20,          -- Default duration in minutes
    elder_weight INT DEFAULT 3,               -- Priority weight for elders
    appointment_weight INT DEFAULT 2,         -- Priority weight for appointments
    wait_time_weight DECIMAL(2,1) DEFAULT 0.1, -- Weight per minute waited
    max_queue_size INT DEFAULT 100,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_service_code (service_code),
    INDEX idx_status (status)
);

-- =============================================
-- Locations Table
-- Stores service locations/branches
-- =============================================
CREATE TABLE locations (
    location_id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    location_name VARCHAR(100) NOT NULL,
    address TEXT,
    operating_hours_start TIME DEFAULT '09:00:00',
    operating_hours_end TIME DEFAULT '17:00:00',
    counters_count INT DEFAULT 4,
    status ENUM('active', 'inactive') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    INDEX idx_service_id (service_id),
    INDEX idx_status (status)
);

-- =============================================
-- Staff Table
-- Stores staff details
-- =============================================
CREATE TABLE staff (
    staff_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    employee_id VARCHAR(20) UNIQUE,
    department VARCHAR(100),
    counter_number INT,
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_available (is_available)
);

-- =============================================
-- Staff-Services Junction Table
-- Assigns services to staff
-- =============================================
CREATE TABLE staff_services (
    staff_id INT NOT NULL,
    service_id INT NOT NULL,
    location_id INT NOT NULL,
    PRIMARY KEY (staff_id, service_id, location_id),
    FOREIGN KEY (staff_id) REFERENCES staff(staff_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE
);

-- =============================================
-- Appointments Table
-- Stores all appointments with flexible time windows
-- =============================================
CREATE TABLE appointments (
    appointment_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    location_id INT NOT NULL,
    appointment_date DATE NOT NULL,
    time_window_start TIME NOT NULL,        -- Flexible window start (e.g., 10:00)
    time_window_end TIME NOT NULL,          -- Flexible window end (e.g., 10:20)
    status ENUM('scheduled', 'checked_in', 'completed', 'cancelled', 'no_show') DEFAULT 'scheduled',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_appointment_date (appointment_date),
    INDEX idx_status (status)
);

-- =============================================
-- Queue Elder Table
-- Stores elder/priority queue entries
-- =============================================
CREATE TABLE queue_elder (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,                              -- NULL for staff-registered elders
    service_id INT NOT NULL,
    location_id INT NOT NULL,
    appointment_id INT,                       -- Link to appointment if applicable
    token VARCHAR(20) NOT NULL,
    priority_score DECIMAL(5,2) DEFAULT 0,    -- Calculated weighted priority
    is_emergency BOOLEAN DEFAULT FALSE,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    called_time TIMESTAMP NULL,
    served_time TIMESTAMP NULL,
    counter_number INT,
    status ENUM('waiting', 'called', 'serving', 'served', 'no_show', 'cancelled') DEFAULT 'waiting',
    elder_name VARCHAR(100),                  -- For staff-registered elders
    elder_phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    INDEX idx_service_location (service_id, location_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority_score),
    INDEX idx_check_in (check_in_time)
);

-- =============================================
-- Queue Normal Table
-- Stores normal queue entries
-- =============================================
CREATE TABLE queue_normal (
    queue_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    service_id INT NOT NULL,
    location_id INT NOT NULL,
    appointment_id INT,
    token VARCHAR(20) NOT NULL,
    priority_score DECIMAL(5,2) DEFAULT 0,
    is_emergency BOOLEAN DEFAULT FALSE,
    check_in_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    called_time TIMESTAMP NULL,
    served_time TIMESTAMP NULL,
    counter_number INT,
    status ENUM('waiting', 'called', 'serving', 'served', 'no_show', 'cancelled') DEFAULT 'waiting',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    FOREIGN KEY (appointment_id) REFERENCES appointments(appointment_id) ON DELETE SET NULL,
    INDEX idx_service_location (service_id, location_id),
    INDEX idx_status (status),
    INDEX idx_priority (priority_score),
    INDEX idx_check_in (check_in_time)
);

-- =============================================
-- Analytics Table
-- Stores daily analytics data
-- =============================================
CREATE TABLE analytics (
    analytics_id INT AUTO_INCREMENT PRIMARY KEY,
    service_id INT NOT NULL,
    location_id INT NOT NULL,
    date DATE NOT NULL,
    total_served INT DEFAULT 0,
    total_elder_served INT DEFAULT 0,
    total_no_shows INT DEFAULT 0,
    avg_wait_time_minutes INT DEFAULT 0,
    peak_hour INT,
    appointments_count INT DEFAULT 0,
    walk_ins_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (service_id) REFERENCES services(service_id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(location_id) ON DELETE CASCADE,
    UNIQUE KEY unique_daily (service_id, location_id, date),
    INDEX idx_date (date)
);

-- =============================================
-- Insert Default Data
-- =============================================

-- Default Admin User (password: Admin@123)
INSERT INTO users (username, name, password_hash, phone, age, category, role) VALUES
('admin', 'System Admin', '$2b$12$xC4u2Tl6aEb31t2xqxghL.Lb3ummkB2zkUwb5bIc9DMTyx5t2xwP.', '1234567890', 35, 'normal', 'admin');

-- Default Staff Users (password: Staff@123)
INSERT INTO users (username, name, password_hash, phone, age, category, role) VALUES
('johnsmith', 'John Smith', '$2b$12$vopPRMcFD4EvtMfxstg7N.fYC133GkC2L.YJKK43u60padenfbEiy', '1234567891', 28, 'normal', 'staff'),
('sarahjohnson', 'Sarah Johnson', '$2b$12$vopPRMcFD4EvtMfxstg7N.fYC133GkC2L.YJKK43u60padenfbEiy', '1234567892', 32, 'normal', 'staff'),
('mikewilson', 'Mike Wilson', '$2b$12$vopPRMcFD4EvtMfxstg7N.fYC133GkC2L.YJKK43u60padenfbEiy', '1234567893', 30, 'normal', 'staff');

-- Default Regular Users (password: Username@123 - e.g. Alicebrown@123)
INSERT INTO users (username, name, password_hash, phone, age, category, role) VALUES
('alicebrown', 'Alice Brown', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4a5U5F5eQJYyL5Iy', '1234567894', 45, 'normal', 'user'),
('bobelder', 'Bob Elder', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4a5U5F5eQJYyL5Iy', '1234567895', 68, 'elder', 'user'),
('carolsenior', 'Carol Senior', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4a5U5F5eQJYyL5Iy', '1234567896', 72, 'elder', 'user');

-- Default Services
INSERT INTO services (service_name, service_code, description, service_duration, elder_weight, appointment_weight) VALUES
('Hospital - OPD', 'HOSP', 'General Outpatient Department', 15, 4, 2),
('Hospital - Laboratory', 'LAB', 'Blood Tests and Diagnostics', 10, 3, 2),
('Bank - Savings Account', 'BANK', 'Savings Account Services', 20, 3, 2),
('Bank - Loans', 'LOAN', 'Loan Application and Processing', 30, 3, 2),
('Government - Documents', 'GDOC', 'Document Verification and Issuance', 25, 4, 2),
('Government - Registrations', 'GREG', 'Registration Services', 20, 4, 2),
('Railway - Ticket Booking', 'RAIL', 'Train Ticket Reservations', 10, 3, 2),
('Railway - Enquiry', 'RENQ', 'Train Schedule and Enquiry', 5, 3, 1);

-- Default Locations
INSERT INTO locations (service_id, location_name, address, counters_count) VALUES
(1, 'City Hospital Main', '123 Healthcare Street, Medical District', 6),
(1, 'City Hospital Branch', '456 Wellness Avenue, North Zone', 4),
(2, 'Central Lab', '123 Healthcare Street, Medical District', 3),
(3, 'Main Bank Branch', '789 Financial Plaza, City Center', 8),
(3, 'Bank North Branch', '101 Commerce Road, North Zone', 4),
(4, 'Main Bank Branch', '789 Financial Plaza, City Center', 4),
(5, 'Government Office Central', '555 Admin Building, Civic Center', 10),
(6, 'Government Office Central', '555 Admin Building, Civic Center', 6),
(7, 'Central Railway Station', '999 Railway Road, Central Station', 12),
(8, 'Central Railway Station', '999 Railway Road, Central Station', 4);

-- Staff Assignments
INSERT INTO staff (user_id, employee_id, department, counter_number) VALUES
(2, 'EMP001', 'Hospital', 1),
(3, 'EMP002', 'Bank', 1),
(4, 'EMP003', 'Government', 1);

-- Staff Service Assignments
INSERT INTO staff_services (staff_id, service_id, location_id) VALUES
(1, 1, 1),  -- John assigned to Hospital OPD
(1, 2, 3),  -- John also handles Lab
(2, 3, 4),  -- Sarah assigned to Bank Savings
(2, 4, 6),  -- Sarah also handles Loans
(3, 5, 7),  -- Mike assigned to Government Documents
(3, 6, 8);  -- Mike also handles Registrations

-- =============================================
-- Stored Procedures for Queue Operations
-- =============================================

DELIMITER //

-- Procedure to get next token number
CREATE PROCEDURE GetNextToken(
    IN p_service_id INT,
    IN p_location_id INT,
    IN p_queue_type VARCHAR(10),
    OUT p_token VARCHAR(20)
)
BEGIN
    DECLARE v_service_code VARCHAR(10);
    DECLARE v_last_num INT DEFAULT 0;
    DECLARE v_prefix VARCHAR(5);
    
    -- Get service code
    SELECT service_code INTO v_service_code FROM services WHERE service_id = p_service_id;
    
    -- Set prefix based on queue type
    IF p_queue_type = 'elder' THEN
        SET v_prefix = CONCAT(v_service_code, '-E');
        -- Get last token number from elder queue
        SELECT COALESCE(MAX(CAST(SUBSTRING(token, LENGTH(v_prefix) + 1) AS UNSIGNED)), 0)
        INTO v_last_num
        FROM queue_elder
        WHERE service_id = p_service_id AND location_id = p_location_id
        AND DATE(check_in_time) = CURDATE();
    ELSE
        SET v_prefix = CONCAT(v_service_code, '-N');
        -- Get last token number from normal queue
        SELECT COALESCE(MAX(CAST(SUBSTRING(token, LENGTH(v_prefix) + 1) AS UNSIGNED)), 0)
        INTO v_last_num
        FROM queue_normal
        WHERE service_id = p_service_id AND location_id = p_location_id
        AND DATE(check_in_time) = CURDATE();
    END IF;
    
    -- Generate new token
    SET p_token = CONCAT(v_prefix, LPAD(v_last_num + 1, 4, '0'));
END //

-- Procedure to calculate priority score
CREATE PROCEDURE CalculatePriorityScore(
    IN p_user_id INT,
    IN p_service_id INT,
    IN p_has_appointment BOOLEAN,
    IN p_is_elder BOOLEAN,
    OUT p_score DECIMAL(5,2)
)
BEGIN
    DECLARE v_elder_weight INT DEFAULT 3;
    DECLARE v_appt_weight INT DEFAULT 2;
    
    -- Get service weights
    SELECT elder_weight, appointment_weight 
    INTO v_elder_weight, v_appt_weight
    FROM services WHERE service_id = p_service_id;
    
    SET p_score = 0;
    
    -- Add elder weight
    IF p_is_elder THEN
        SET p_score = p_score + v_elder_weight;
    END IF;
    
    -- Add appointment weight
    IF p_has_appointment THEN
        SET p_score = p_score + v_appt_weight;
    END IF;
END //

DELIMITER ;

-- =============================================
-- View for Current Queue Status
-- =============================================
CREATE OR REPLACE VIEW v_current_queue AS
SELECT 
    'elder' as queue_type,
    qe.queue_id,
    qe.token,
    qe.user_id,
    COALESCE(u.name, qe.elder_name) as user_name,
    qe.service_id,
    s.service_name,
    qe.location_id,
    l.location_name,
    qe.priority_score,
    qe.is_emergency,
    qe.check_in_time,
    qe.status,
    qe.counter_number
FROM queue_elder qe
LEFT JOIN users u ON qe.user_id = u.user_id
JOIN services s ON qe.service_id = s.service_id
JOIN locations l ON qe.location_id = l.location_id
WHERE qe.status IN ('waiting', 'called', 'serving')
AND DATE(qe.check_in_time) = CURDATE()

UNION ALL

 SELECT 
    'normal' as queue_type,
    qn.queue_id,
    qn.token,
    qn.user_id,
    u.name as user_name,
    qn.service_id,
    s.service_name,
    qn.location_id,
    l.location_name,
    qn.priority_score,
    qn.is_emergency,
    qn.check_in_time,
    qn.status,
    qn.counter_number
FROM queue_normal qn
JOIN users u ON qn.user_id = u.user_id
JOIN services s ON qn.service_id = s.service_id
JOIN locations l ON qn.location_id = l.location_id
WHERE qn.status IN ('waiting', 'called', 'serving')
AND DATE(qn.check_in_time) = CURDATE()

ORDER BY is_emergency DESC, priority_score DESC, check_in_time ASC;

-- =============================================
-- Indexes for performance
-- =============================================
CREATE INDEX idx_queue_elder_date ON queue_elder(check_in_time);
CREATE INDEX idx_queue_normal_date ON queue_normal(check_in_time);
CREATE INDEX idx_appointments_user_date ON appointments(user_id, appointment_date);

-- =============================================
-- End of Schema
-- =============================================
