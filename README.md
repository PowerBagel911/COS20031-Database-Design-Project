# 🏹 Archery Club Database Application

A comprehensive database management system for archery clubs to track archers, scores, competitions, and more. Built with Streamlit and MySQL, this application provides a user-friendly interface for club administration and archer performance tracking.

## 📋 Table of Contents
- [Overview](#overview)
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)
- [Role-Based Access](#role-based-access)
- [Database Schema](#database-schema)
- [Security](#security)
- [Development](#development)
- [Contributors](#contributors)

## 🔍 Overview

The Archery Club Database Application is designed to streamline the management of archery club operations, including member management, score tracking, competition organization, and performance analysis. The system supports different user roles (Archers, Recorders, and Administrators) with appropriate access levels and features.

## ✨ Features

### Archer Features
- **View Personal Scores**: Track performance over time with detailed score history
- **Record Practice Scores**: Submit practice scores for approval
- **View Round Definitions**: Access information about different archery round types
- **View Competition Results**: Check competition standings and personal performance

### Recorder Features
- **Manage Archers**: Add new archers, update archer information
- **Approve Practice Scores**: Review and approve scores submitted by archers
- **Manage Competitions**: Create and organize competitions
- **Generate Competition Results**: Calculate and publish competition results

### Administrator Features
- **SQL Assistant**: AI-powered database query tool using Google's Gemini 2.0 Flash API
- **User Management**: Create and manage user accounts
- **Permission Management**: Control access rights for users
- **Security Logs**: Monitor system activity and security events
- **Account Management**: Update user information and password

## 🏗️ System Architecture

### Frontend
- **Streamlit**: Web interface framework providing interactive dashboards and forms
- **Pandas**: For data manipulation and display

### Backend
- **MySQL Database**: Stores all application data
- **Stored Procedures**: Business logic for data operations
- **Python Middleware**: Connects frontend to backend services

### Integration
- **Google Generative AI (Gemini 2.0 Flash)**: Powers the SQL Assistant feature

## 💾 Installation

### Prerequisites
- Python 3.9 or higher
- MySQL Server 8.0 or higher
- Swinburne VPN access (for database connectivity)

### Setup Steps

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd COS20031-Database-Design-Project
   ```

2. **Install required packages**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up database**:
   - Run `create_tables.sql` to create the database schema
   - Run `create_procedures.sql` to create the stored procedures and indexes

4. **Create a Streamlit secrets file** (`secrets.toml` in the `.streamlit` folder):
   ```toml
   [DEFAULT]
   DB_HOST = "your-db-host"
   DB_USER = "your-db-user"
   DB_PASSWORD = "your-db-password"
   DB_NAME = "your-db-name"
   GEMINI_API_KEY = "your-gemini-api-key"
   ```

5. **Run the application**:
   ```bash
   streamlit run app.py
   ```

## 🚀 Usage

1. **Login**: Access the system with your username and password
2. **Dashboard**: Navigate through the main dashboard to access various features
3. **Menu**: Use the sidebar menu to switch between different functionalities
4. **Logout**: End your session securely

## 👥 Role-Based Access

The application implements three distinct user roles:

- **Archers**: Regular club members who can view and record scores
- **Recorders**: Club officials who can manage archers, approve scores, and organize competitions
- **Administrators**: System administrators with full access to all features including security monitoring and database management

## 📊 Database Schema

The database includes tables for:

- User accounts and authentication
- Archer profiles and equipment types
- Competition definitions and results
- Score tracking and approval
- Round types and specifications
- Security logging and auditing

## 🔒 Security

The application implements various security measures:

- **Salted password hashing**: Secure storage of user credentials
- **Input validation**: Protection against invalid data and injection attacks
- **Security logging**: Comprehensive audit trail of system activities
- **Role-based access control**: Ensures users only access authorized features
- **SQL query inspection**: Prevention of dangerous database operations

## 💻 Development

### Project Structure

```
app.py                  # Main application entry point
create_procedures.sql   # Database stored procedures
create_tables.sql       # Database schema definitions
requirements.txt        # Python dependencies
archery_app/
  ├── __init__.py       # Package initialization
  ├── admin_pages.py    # Admin-specific features
  ├── archer_pages.py   # Archer-specific features
  ├── auth.py           # Authentication system
  ├── chatbot.py        # SQL Assistant feature
  ├── database.py       # Database connectivity
  ├── recorder_pages.py # Recorder-specific features
  ├── security_admin.py # Security administration
  ├── security_logging.py # Security event logging
  └── validators.py     # Input validation functions
```

### Technologies Used

- **Python**: Main programming language
- **Streamlit**: Web application framework
- **MySQL Connector**: Database connectivity
- **SQLAlchemy**: ORM for database operations
- **Pandas**: Data manipulation and display
- **Google Generative AI**: AI chat assistance

## 👨‍💻 Contributors

- COS20031 Database Design Project Team
- Swinburne University of Technology

---

© 2025 Archery Club Database Project | Swinburne University of Technology
