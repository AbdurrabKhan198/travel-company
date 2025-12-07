# Server Environment Variables Setup

## Brevo API Key Setup on Server

### Step 1: SSH to Server
```bash
ssh safar@165.232.178.54
```

### Step 2: Set Environment Variable

**Option A: Add to systemd service file (Recommended)**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add this line in `[Service]` section:
```ini
Environment="BREVO_API_KEY=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"
```

Then reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

**Option B: Add to .env file (if using python-dotenv)**
```bash
cd /var/www/safarzonetravels
nano .env
```

Add:
```
BREVO_API_KEY=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
```

**Option C: Export in shell (temporary - only for current session)**
```bash
export BREVO_API_KEY='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'
```

### Step 3: Verify
```bash
# Check if variable is set
echo $BREVO_API_KEY

# Restart gunicorn
sudo systemctl restart gunicorn

# Check logs
tail -f logs/email.log
```

### Step 4: Test
Try signup OTP - should work now!

## Important Notes

1. **Never commit API keys to Git** - always use environment variables
2. **Option A (systemd) is best** - persists across reboots
3. **Keep API key secret** - don't share or expose it

