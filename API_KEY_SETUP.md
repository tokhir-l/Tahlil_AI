# API Key Setup Guide

## Overview

The platform requires a **Gemini API Key** to function. The hardcoded default key has been removed for security and best practices.

## Getting Your API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Setting Up Your API Key

### Method 1: .env File (Recommended) ✅

1. Create a `.env` file in the project root directory:
   ```
   Tahlil/
   ├── .env          ← Create this file
   ├── app.py
   ├── tahlil.py
   └── ...
   ```

2. Add your API key to the `.env` file:
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

3. Install python-dotenv (optional but recommended):
   ```bash
   pip install python-dotenv
   ```

4. The `.env` file is already in `.gitignore`, so it won't be committed to git.

### Method 2: Environment Variable

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY = "your-api-key-here"
python app.py
```

#### Windows (CMD)
```cmd
set GEMINI_API_KEY=your-api-key-here
python app.py
```

#### Linux/Mac
```bash
export GEMINI_API_KEY="your-api-key-here"
python app.py
```

### Method 3: System Environment Variable (Permanent)

Set it in your system environment variables so it persists across sessions.

## Verification

When you start Flask, you should see:
```
✅ GEMINI_API_KEY is set (length: 39)
```

If you see an error instead, the API key is not set correctly.

## Security Notes

- ✅ `.env` file is in `.gitignore` - your key won't be committed
- ✅ Never commit API keys to version control
- ✅ Never share your API key publicly
- ✅ Rotate your API key if it's exposed

## Troubleshooting

**Error: "GEMINI_API_KEY environment variable is required"**
- Make sure you've set the API key using one of the methods above
- Restart Flask after setting the environment variable
- Check that the `.env` file is in the project root (same directory as `app.py`)

**Error: "Missing API key for gemini-..."**
- The API key might not be passed to subprocesses correctly
- Make sure the environment variable is set before starting Flask

## Optional: Install python-dotenv

For automatic `.env` file loading:
```bash
pip install python-dotenv
```

This allows Flask to automatically load the `.env` file when starting.

