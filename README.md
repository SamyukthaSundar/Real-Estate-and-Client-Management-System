#  Real Estate and Client Management System

## Description
This project is a robust **Database Management System (DBMS)** designed to efficiently manage the core operations of a real estate agency. It provides structured storage and retrieval for properties, clients, agents, and transactions, enabling quick access to critical business data.

The system is built using **Python** for the backend logic and features comprehensive **SQL** components—including a detailed schema, stored functions, triggers, and procedures—to ensure data integrity and efficient query performance.

##  Key Features
* **Property Management:** Track property listings, status (available, sold, pending), and detailed information (address, price, size, features).
* **Client Relationship Management (CRM):** Maintain detailed records of buyers and sellers, including contact information and preference profiles.
* **Transaction Tracking:** Record and manage sales, commissions, and closing dates.
* **Database Integrity:** Utilizes Stored Procedures, Functions, and Triggers (in `func_trig_proc.sql`) to enforce business rules and automate database operations.
* **User Interface:** Includes a separate frontend component for user interaction and data visualization.

##  Project Structure
* **`app.py`**: The main entry point for the Python backend application.
* **`db/`**: Contains database configuration and connection logic.
* **`frontend/`**: Holds the user interface code (HTML/CSS/JS).
* **`utils/`**: Helper functions and utility scripts used across the application.
* **`database_schema.sql`**: Defines the database tables and relationships.
* **`func_trig_proc.sql`**: Contains the stored procedures, triggers, and functions.
* **`requirements.txt`**: List of Python dependencies required to run the project.

##  Technologies Used
* **Language:** Python 3.x
* **Database:** MySQL
* **Backend:** Python (Flask/Standard Library)
* **Frontend:** HTML/CSS/JavaScript (located in `frontend/` directory)

##  Installation and Setup

Follow these steps to set up the project locally.

### Prerequisites
You will need the following installed:
* Python 3.x
* A SQL Database Server (MySQL)
* pip (Python package installer)

### Installation Steps

1. Clone the repository:
```bash
git clone [https://github.com/SamyukthaSundar/real-estate-mgmt.git](https://github.com/SamyukthaSundar/real-estate-mgmt.git)
cd real-estate-mgmt
cd real-estate-mgmt
 2. Install Python Dependencies:
     pip install -r requirements.txt
3. Database Configuration:
     CREATE DATABASE realestate_db;
4. Initialize the Schema and Logic:
    # Create tables
    mysql -u root -p realestate_db < database_schema.sql

  # Import functions, triggers, and procedures
     mysql -u root -p realestate_db < func_trig_proc.sql

5. Start the Backend Application:
    python app.py
Contact
Samyuktha S - samyukthasundarrajan@gmail.com
Samiya Naaz - samiya09naaz@gmail.com


