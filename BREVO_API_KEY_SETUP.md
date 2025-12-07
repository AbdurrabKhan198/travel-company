# Brevo API Key Setup - IMPORTANT!

## Problem
You're getting `401 - Key not found` error because you're using **SMTP key** but Brevo API needs **API key** (they are different!).

## Solution: Get API Key

### Step 1: Login to Brevo
Go to: https://app.brevo.com/

### Step 2: Go to API Keys Page
Click: **Settings** → **API Keys** (NOT SMTP Settings!)
Direct link: https://app.brevo.com/settings/keys/api

### Step 3: Create New API Key
1. Click **"Generate a new API key"**
2. Give it a name (e.g., "Travel Agency API")
3. Select permissions: **"Send emails"** or **"Full access"**
4. Click **"Generate"**
5. **COPY THE KEY IMMEDIATELY** - you won't see it again!

### Step 4: Update Settings

**Option A: Add to settings.py (temporary for testing)**
```python
BREVO_API_KEY = 'YOUR_NEW_API_KEY_HERE'  # From API Keys page
```

**Option B: Set as environment variable (recommended for production)**
```bash
export BREVO_API_KEY='YOUR_NEW_API_KEY_HERE'
```

### Step 5: Restart Server
```bash
sudo systemctl restart gunicorn
```

## Key Differences

| Type | Where to Get | Format | Use Case |
|------|-------------|--------|----------|
| **API Key** | https://app.brevo.com/settings/keys/api | Usually starts with `xkeysib-` or similar | HTTP API (what we need) |
| **SMTP Key** | https://app.brevo.com/settings/smtp | Starts with `xsmtpsib-` | SMTP only (blocked by DigitalOcean) |

## Current Issue
You're using SMTP key (`xsmtpsib-...`) but need API key for HTTP API.

## After Getting API Key
1. Update `BREVO_API_KEY` in settings.py or environment variable
2. Restart server
3. Test signup OTP again
4. Check logs: `tail -f logs/email.log`

## Need Help?
- Brevo API Docs: https://developers.brevo.com/docs
- API Key Guide: https://help.brevo.com/hc/en-us/articles/209467485-How-to-create-an-API-key

