-- Create Database
CREATE DATABASE real_estate_mgmt;

-- Use Database
USE real_estate_mgmt;

-- ========================
-- Users Table
-- ========================
CREATE TABLE Users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15),
    role ENUM('Admin', 'Agent', 'Client') NOT NULL,
    password VARCHAR(255) NOT NULL
);

INSERT INTO Users (name, email, phone, role, password) VALUES
('Admin One', 'admin1@example.com', '9876543210', 'Admin', 'admin123'),
('Agent John', 'agentjohn@example.com', '9876501234', 'Agent', 'agent123'),
('Client Mary', 'mary@example.com', '9876512345', 'Client', 'client123');

-- ========================
-- Properties Table
-- ========================
CREATE TABLE Properties (
    property_id INT PRIMARY KEY AUTO_INCREMENT,
    agent_id INT,
    title VARCHAR(150) NOT NULL,
    type ENUM('Buy', 'Rent', 'Sell') NOT NULL,
    price DECIMAL(12,2) NOT NULL,
    location VARCHAR(255),
    building_age INT,
    status ENUM('Available', 'Booked', 'Sold', 'Rented') NOT NULL,
    FOREIGN KEY (agent_id) REFERENCES Users(user_id)
);

INSERT INTO Properties (agent_id, title, type, price, location, building_age, status) VALUES
(2, '2BHK Apartment in City Center', 'Sell', 4500000, 'Bangalore', 5, 'Available'),
(2, 'Luxury Villa with Garden', 'Rent', 75000, 'Hyderabad', 2, 'Booked');

-- ========================
-- Appointments Table
-- ========================
CREATE TABLE Appointments (
    appointment_id INT PRIMARY KEY AUTO_INCREMENT,
    property_id INT,
    user_id INT,
    agent_id INT,
    datetime DATETIME NOT NULL,
    status ENUM('Pending', 'Confirmed', 'Completed', 'Cancelled') NOT NULL,
    FOREIGN KEY (property_id) REFERENCES Properties(property_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (agent_id) REFERENCES Users(user_id)
);

INSERT INTO Appointments (property_id, user_id, agent_id, datetime, status) VALUES
(1, 3, 2, '2025-09-20 10:00:00', 'Pending'),
(2, 3, 2, '2025-09-21 15:30:00', 'Confirmed');



-- ========================
-- Buys Table
-- ========================
CREATE TABLE Buys (
    buyer_id INT,
    property_id INT,
    date DATE NOT NULL,
    amount DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (buyer_id, property_id),
    FOREIGN KEY (buyer_id) REFERENCES Users(user_id),
    FOREIGN KEY (property_id) REFERENCES Properties(property_id)
);

INSERT INTO Buys (buyer_id, property_id, date, amount) VALUES
(3, 1, '2025-09-25', 4500000),
(3, 2, '2025-09-28', 75000);

-- ========================
-- Rents Table
-- ========================
CREATE TABLE Rents (
    tenant_id INT,
    property_id INT,
    rent_amount DECIMAL(12,2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    PRIMARY KEY (tenant_id, property_id),
    FOREIGN KEY (tenant_id) REFERENCES Users(user_id),
    FOREIGN KEY (property_id) REFERENCES Properties(property_id)
);

INSERT INTO Rents (tenant_id, property_id, rent_amount, start_date, end_date) VALUES
(3, 2, 75000, '2025-09-01', '2026-08-31'),
(3, 1, 50000, '2025-10-01', '2026-09-30');

-- ========================
-- Reviews Table
-- ========================
CREATE TABLE Reviews (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    property_id INT,
    agent_id INT,
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comments TEXT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (property_id) REFERENCES Properties(property_id),
    FOREIGN KEY (agent_id) REFERENCES Users(user_id)
);

INSERT INTO Reviews (user_id, property_id, agent_id, rating, comments) VALUES
(3, 1, 2, 5, 'Excellent property, smooth process!'),
(3, 2, 2, 4, 'Good villa, but a bit pricey.');


-- ==============================================
-- ADDING CONSTRAINTS AND DEFAULTS FOR ALL TABLES
-- ==============================================

USE real_estate_mgmt;

-- ========================
-- USERS TABLE
-- ========================
ALTER TABLE Users
MODIFY role ENUM('Admin', 'Agent', 'Client') NOT NULL DEFAULT 'Client',
ADD CONSTRAINT chk_phone_length CHECK (CHAR_LENGTH(phone) BETWEEN 10 AND 15);

-- ========================
-- PROPERTIES TABLE
-- ========================
ALTER TABLE Properties
MODIFY status ENUM('Available', 'Booked', 'Sold', 'Rented') NOT NULL DEFAULT 'Available',
ADD CONSTRAINT chk_price_positive CHECK (price > 0);

-- Update foreign key with ON DELETE SET NULL
ALTER TABLE Properties
DROP FOREIGN KEY Properties_ibfk_1,
ADD CONSTRAINT fk_agent_property FOREIGN KEY (agent_id)
REFERENCES Users(user_id) ON DELETE SET NULL;

-- ========================
-- APPOINTMENTS TABLE
-- ========================
ALTER TABLE Appointments
MODIFY status ENUM('Pending', 'Confirmed', 'Completed', 'Cancelled') NOT NULL DEFAULT 'Pending';

-- Drop existing FKs if necessary and recreate with ON DELETE CASCADE
ALTER TABLE Appointments
DROP FOREIGN KEY Appointments_ibfk_1,
DROP FOREIGN KEY Appointments_ibfk_2,
DROP FOREIGN KEY Appointments_ibfk_3,
ADD CONSTRAINT fk_app_property FOREIGN KEY (property_id) REFERENCES Properties(property_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_app_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_app_agent FOREIGN KEY (agent_id) REFERENCES Users(user_id) ON DELETE CASCADE;

-- ========================
-- OWNS TABLE
-- ========================
ALTER TABLE Owns
DROP FOREIGN KEY Owns_ibfk_1,
DROP FOREIGN KEY Owns_ibfk_2,
ADD CONSTRAINT fk_owns_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_owns_property FOREIGN KEY (property_id) REFERENCES Properties(property_id) ON DELETE CASCADE;

-- ========================
-- BUYS TABLE
-- ========================
ALTER TABLE Buys
ADD CONSTRAINT chk_amount_positive CHECK (amount > 0);

ALTER TABLE Buys
DROP FOREIGN KEY Buys_ibfk_1,
DROP FOREIGN KEY Buys_ibfk_2,
ADD CONSTRAINT fk_buy_user FOREIGN KEY (buyer_id) REFERENCES Users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_buy_property FOREIGN KEY (property_id) REFERENCES Properties(property_id) ON DELETE CASCADE;

-- ========================
-- RENTS TABLE
-- ========================
ALTER TABLE Rents
ADD CONSTRAINT chk_rent_positive CHECK (rent_amount > 0),
ADD CONSTRAINT chk_rent_dates CHECK (end_date IS NULL OR end_date > start_date);

ALTER TABLE Rents
DROP FOREIGN KEY Rents_ibfk_1,
DROP FOREIGN KEY Rents_ibfk_2,
ADD CONSTRAINT fk_rent_user FOREIGN KEY (tenant_id) REFERENCES Users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_rent_property FOREIGN KEY (property_id) REFERENCES Properties(property_id) ON DELETE CASCADE;

-- ========================
-- REVIEWS TABLE
-- ========================
ALTER TABLE Reviews
MODIFY rating INT DEFAULT 3 CHECK (rating BETWEEN 1 AND 5);

ALTER TABLE Reviews
DROP FOREIGN KEY Reviews_ibfk_1,
DROP FOREIGN KEY Reviews_ibfk_2,
DROP FOREIGN KEY Reviews_ibfk_3,
ADD CONSTRAINT fk_rev_user FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_rev_property FOREIGN KEY (property_id) REFERENCES Properties(property_id) ON DELETE CASCADE,
ADD CONSTRAINT fk_rev_agent FOREIGN KEY (agent_id) REFERENCES Users(user_id) ON DELETE CASCADE;
