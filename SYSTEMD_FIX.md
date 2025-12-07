# 🔧 Systemd Service Fix - Brevo Credentials

## Problem
Application runs via systemd/supervisor, so shell environment variables don't work!

## Solution: Add to Systemd Service File

### Step 1: Find Your Service File

```bash
# Check what service is running
sudo systemctl status gunicorn
# Or
sudo systemctl status uwsgi
# Or check supervisor
sudo supervisorctl status
```

### Step 2: Edit Service File

**If using systemd:**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**If using supervisor:**
```bash
sudo nano /etc/supervisor/conf.d/gunicorn.conf
```

### Step 3: Add Environment Variables

**For systemd** - Add these lines under `[Service]` section:

```ini
[Service]
Environment="BREVO_SMTP_USER=noreply@safarzonetravels.com"
Environment="BREVO_SMTP_KEY=xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

**For supervisor** - Add to `environment` line:

```ini
[program:gunicorn]
environment=BREVO_SMTP_USER="noreply@safarzonetravels.com",BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

### Step 4: Reload and Restart

**For systemd:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
sudo systemctl status gunicorn
```

**For supervisor:**
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart gunicorn
```

### Step 5: Test

Try signup OTP - should work now!

---

## Complete Example: systemd Service File

```ini
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=safar
Group=www-data
WorkingDirectory=/var/www/safarzonetravels
ExecStart=/var/www/safarzonetravels/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/safarzonetravels/gunicorn.sock Travel_agency.wsgi:application

# BREVO CREDENTIALS - ADD THESE LINES!
Environment="BREVO_SMTP_USER=noreply@safarzonetravels.com"
Environment="BREVO_SMTP_KEY=xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"

Restart=always

[Install]
WantedBy=multi-user.target
```

**After editing, save and:**
```bash
sudo systemctl daemon-reload
sudo systemctl restart gunicorn
```

---

## Verify It's Working

```bash
# Check logs
tail -f logs/email.log

# Try signup - OTP should work!
```

