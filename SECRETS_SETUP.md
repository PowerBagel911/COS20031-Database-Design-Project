# Setting Up Streamlit Secrets

This document explains how to set up Streamlit secrets for the Archery Club Database application.

## Why Secrets?

The application uses Streamlit's secrets management to securely store sensitive information such as:
- Database credentials
- API keys for external services

These secrets should never be committed to version control (which is why they're in `.gitignore`).

## Local Development Setup

For local development, you need to create a `.streamlit/secrets.toml` file:

1. Create a `.streamlit` directory in your project root (if it doesn't exist)
2. Create a `secrets.toml` file inside this directory
3. Add the following configuration, replacing placeholders with your actual credentials:

```toml
# Database Configuration
DB_HOST = "your-database-host"
DB_USER = "your-database-username"
DB_PASSWORD = "your-database-password"
DB_NAME = "your-database-name"

# API Keys
DEEPSEEK_API_KEY = "your-deepseek-api-key"
```

For example:
```toml
# Database Configuration
DB_HOST = "feenix-mariadb.swin.edu.au"
DB_USER = "s123456789"
DB_PASSWORD = "your-actual-password"
DB_NAME = "s123456789_db"

# API Keys
DEEPSEEK_API_KEY = "sk-your-actual-api-key"
```

## Streamlit Cloud Deployment

When deploying to Streamlit Cloud:

1. **Do not push** your local `secrets.toml` file to GitHub or other version control (it's already in `.gitignore`)

2. Add your secrets through the Streamlit Cloud dashboard:
   - Go to your app's page on Streamlit Cloud
   - Click on "Settings" > "Secrets"
   - Add the same configuration from your local `secrets.toml` file

## Additional Considerations

- Keep your secrets secure; never share them publicly
- If you believe your secrets have been compromised, rotate them immediately
- For team development, share secrets through secure channels like password managers, not through email or messaging apps

## Troubleshooting

If you encounter issues related to secrets:

1. **Local development**: Check that your `secrets.toml` file exists in the `.streamlit` directory and contains the correct values
2. **Streamlit Cloud**: Verify that you've added the secrets in the Streamlit Cloud dashboard correctly
3. **Connection errors**: Double-check that your database credentials are correct and that the database server is accessible from your environment

For database connection issues, make sure your database server allows connections from your IP address or the Streamlit Cloud servers.
