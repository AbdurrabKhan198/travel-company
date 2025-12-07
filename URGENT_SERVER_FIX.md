# 🚨 URGENT: Server Email Fix - Nothing Working

## Problem
- ❌ Signup OTP not working
- ❌ Password reset not working  
- ❌ All emails timing out
- **Reason**: Brevo credentials NOT set on server

## ⚡ IMMEDIATE FIX (5 minutes)

### Step 1: SSH to Server

```bash
ssh safar@165.232.178.54
```

### Step 2: Go to Project Directory

```bash
cd /var/www/safarzonetravels
```

### Step 3: Set Brevo Credentials (REQUIRED!)

```bash
# Set for current session
export BREVO_SMTP_USER="noreply@safarzonetravels.com"
export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

### Step 4: Make Permanent (IMPORTANT!)

```bash
# Add to .bashrc so it persists
echo 'export BREVO_SMTP_USER="noreply@safarzonetravels.com"' >> ~/.bashrc
echo 'export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"' >> ~/.bashrc

# Reload
source ~/.bashrc
```

### Step 5: Verify Credentials Are Set

```bash
echo $BREVO_SMTP_USER
echo $BREVO_SMTP_KEY
```

**Should show:**
```
noreply@safarzonetravels.com
xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV
```

### Step 6: Restart Application

```bash
# If using systemd
sudo systemctl restart gunicorn

# If using supervisor
sudo supervisorctl restart gunicorn

# Or if using uwsgi
sudo systemctl restart uwsgi

# Check status
sudo systemctl status gunicorn
```

### Step 7: Test Immediately

1. Go to your website
2. Try to signup (OTP should work)
3. Check logs: `tail -f logs/email.log`

## Expected Logs

After setting credentials, you should see:
```
Trying GoDaddy-smtpout-Port2525-TLS: smtpout.secureserver.net:2525
✗ Failed with GoDaddy-smtpout-Port2525-TLS: timed out
Trying Brevo-Port587: smtp-relay.brevo.com:587
✓ Email sent successfully using Brevo-Port587
```

## If Still Not Working

### Check 1: Are credentials actually set?

```bash
# In Django shell
cd /var/www/safarzonetravels
source venv/bin/activate
python manage.py shell
```

Then:
```python
import os
print(os.environ.get('BREVO_SMTP_USER'))
print(os.environ.get('BREVO_SMTP_KEY'))
```

If it shows `None` → Credentials not set properly!

### Check 2: Application Environment

If using systemd/supervisor, you need to set environment variables in the service file:

**For systemd** (`/etc/systemd/system/gunicorn.service`):
```ini
[Service]
Environment="BREVO_SMTP_USER=noreply@safarzonetravels.com"
Environment="BREVO_SMTP_KEY=xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

**For supervisor** (`/etc/supervisor/conf.d/gunicorn.conf`):
```ini
[program:gunicorn]
environment=BREVO_SMTP_USER="noreply@safarzonetravels.com",BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

Then:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart gunicorn
```

## Quick Test Script

Create a test file on server:

```bash
cd /var/www/safarzonetravels
source venv/bin/activate
python manage.py shell
```

Then run:
```python
from django.core.mail import send_mail
from django.conf import settings
import os

print("Brevo User:", os.environ.get('BREVO_SMTP_USER'))
print("Brevo Key:", os.environ.get('BREVO_SMTP_KEY')[:20] + "..." if os.environ.get('BREVO_SMTP_KEY') else "NOT SET")

try:
    send_mail(
        'Test Email',
        'This is a test',
        'noreply@safarzonetravels.com',
        ['your-email@gmail.com'],
        fail_silently=False,
    )
    print("✅ Email sent successfully!")
except Exception as e:
    print(f"❌ Error: {e}")
```

## Most Common Issue

**Problem**: Credentials set in terminal but application doesn't see them

**Solution**: Set in systemd/supervisor service file (see above)

---

## Complete Fix Commands (Copy-Paste)

```bash
# 1. SSH to server
ssh safar@165.232.178.54

# 2. Set credentials
export BREVO_SMTP_USER="noreply@safarzonetravels.com"
export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"

# 3. Make permanent
echo 'export BREVO_SMTP_USER="noreply@safarzonetravels.com"' >> ~/.bashrc
echo 'export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"' >> ~/.bashrc
source ~/.bashrc

# 4. Check systemd service file
sudo nano /etc/systemd/system/gunicorn.service

# Add these lines under [Service]:
# Environment="BREVO_SMTP_USER=noreply@safarzonetravels.com"
# Environment="BREVO_SMTP_KEY=xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"

# 5. Reload and restart
sudo systemctl daemon-reload
sudo systemctl restart gunicorn

# 6. Check status
sudo systemctl status gunicorn
tail -f logs/email.log
```

**After this, emails WILL work!** ✅

