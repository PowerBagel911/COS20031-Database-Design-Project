# Gemini API Setup Guide

This guide will help you set up and use the Gemini API for the Archery Club Database application.

## Step 1: Get a Gemini API Key

1. Go to [Google AI Studio](https://ai.google.dev/) and sign in with your Google account
2. Click on "Get API key" in the top-right corner
3. Create a new API key and make note of it

## Step 2: Add the API Key to Streamlit Secrets

1. For local development:
   - Open `.streamlit/secrets.toml`
   - Replace `YOUR_GEMINI_API_KEY_HERE` with your actual API key:
     ```toml
     GEMINI_API_KEY = "your-actual-api-key"
     ```

2. For Streamlit Cloud deployment:
   - Go to your app's settings in Streamlit Cloud
   - Navigate to the "Secrets" section
   - Make sure the GEMINI_API_KEY is included with your actual API key

## Step 3: Install Required Packages

Install the necessary Python packages:

```bash
pip install -r requirements.txt
```

## Notes on Gemini 2.0 Flash

- Gemini 2.0 Flash is an efficient version of Google's Gemini model
- It provides fast responses for tasks like generating SQL queries
- The model has a good understanding of SQL syntax and database concepts
- API usage is subject to [Google's API pricing](https://ai.google.dev/pricing) (check for latest rates)

## Troubleshooting

If you encounter issues:

1. **API Key Issues**: Ensure your API key is correct and hasn't expired
2. **Model Access**: Make sure your Google account has access to Gemini models
3. **Rate Limits**: Be aware of any rate limits on the free tier of the API
4. **Connection Issues**: Check your internet connection as the API requires online access

For more help, refer to [Google's Generative AI documentation](https://ai.google.dev/docs/gemini-api/)
