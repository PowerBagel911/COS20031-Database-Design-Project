# 🏹 Archery Club Database

A comprehensive database management system for archery clubs, featuring role-based access control, score tracking, competition management, and more.

## Overview

This Streamlit web application provides a user-friendly interface for archers, recorders, and administrators to manage various aspects of an archery club, including:

- **User Authentication**: Secure login with password hashing and salting
- **Score Tracking**: Record and view practice scores
- **Competition Management**: Create, manage, and generate results for competitions
- **Member Management**: Add and manage archer profiles
- **Role-Based Access**: Different functionality for archers, recorders, and administrators
- **SQL Assistant**: AI-powered SQL query assistant for database exploration (admin only)

## Features

### For All Users (Archers)

- **View Personal Scores**: Track historical performance
- **Record Practice Scores**: Submit scores for approval
- **View Round Definitions**: Reference standard archery rounds
- **View Competition Results**: See results from club competitions
- **Account Management**: Update personal account settings

### For Recorders

All archer features, plus:
- **Manage Archers**: Add and edit archer profiles
- **Approve Practice Scores**: Validate submitted scores
- **Manage Competitions**: Create and edit competitions
- **Generate Competition Results**: Calculate and publish results

### For Administrators

All recorder features, plus:
- **User Management**: Create and manage user accounts
- **Permission Management**: Assign recorder/admin privileges
- **SQL Assistant**: AI-powered SQL query interface

## Technical Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: MySQL (MariaDB)
- **Authentication**: Custom implementation with SHA-256 hashing
- **AI Integration**: Deepseek API for SQL assistance

## Database Schema

The database includes tables for:
- Users and authentication
- Archers and their details
- Equipment types
- Age groups and classes
- Rounds and distances
- Practice scores
- Competitions and results

## Installation and Setup

### Prerequisites

- Python 3.10 or higher
- MySQL/MariaDB database server
- Access to Deepseek API (for SQL assistance feature)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/archery-club-database.git
   cd archery-club-database
   ```

2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Streamlit secrets:
   - Create a `.streamlit/secrets.toml` file with the following content:
     ```toml
     # Database Configuration
     DB_HOST = "your-db-host"
     DB_USER = "your-db-user"
     DB_PASSWORD = "your-db-password"
     DB_NAME = "your-db-name"

     # API Keys
     DEEPSEEK_API_KEY = "your-deepseek-api-key"
     ```
   - Replace the placeholder values with your actual credentials

4. Initialize the database:
   - Run the SQL scripts in a MySQL/MariaDB client:
     ```bash
     mysql -u yourusername -p yourdatabase < create_tables.sql
     mysql -u yourusername -p yourdatabase < create_procedures.sql
     ```

5. Run the application:
   ```bash
   streamlit run app.py
   ```

## Deploying to Streamlit Cloud

1. Push your code to GitHub (without the secrets.toml file, which is in .gitignore)

2. Create a new app in Streamlit Cloud pointing to your repository

3. Add your secrets in the Streamlit Cloud dashboard:
   - Go to your app settings
   - Navigate to the "Secrets" section
   - Add the same configuration from your local secrets.toml file:
     ```toml
     # Database Configuration
     DB_HOST = "your-db-host"
     DB_USER = "your-db-user"
     DB_PASSWORD = "your-db-password"
     DB_NAME = "your-db-name"

     # API Keys
     DEEPSEEK_API_KEY = "your-deepseek-api-key"
     ```

## Security Notes

- Passwords are stored with salted SHA-256 hashing
- Connection strings and API keys are stored in Streamlit secrets
- Role-based permissions prevent unauthorized access to features
- SQL Assistant has safeguards against destructive operations

## Usage Guide

### First-Time Setup

1. An administrator should:
   - Create initial user accounts for club members
   - Set up equipment types, rounds, and other reference data
   - Assign recorder privileges to designated users

2. Recorders can then:
   - Add archer profiles for club members
   - Set up competitions
   - Approve practice scores

3. All archers can:
   - Log in and view their personal dashboard
   - Record practice scores
   - View competition results

### Typical Workflows

**Recording Practice Scores:**
1. Archer logs in and navigates to "Record Score"
2. Enters score details and submits
3. Recorder reviews and approves the score
4. Score appears in archer's performance history

**Setting Up Competitions:**
1. Recorder creates a new competition with dates and rounds
2. System automatically determines eligible archers
3. After the competition, recorder generates results
4. Results are published for all users to view

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Streamlit for the web framework
- MySQL/MariaDB for the database engine
- Deepseek for AI assistance capabilities
