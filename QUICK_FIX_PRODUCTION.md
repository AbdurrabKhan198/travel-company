# ⚡ Quick Fix for Production - Email Timeout Error

## Problem
"Error sending password reset email: timed out" - This means Brevo credentials are not set on server.

## Solution: Set Brevo Credentials on Server (2 minutes)

### Step 1: SSH to Your Server

```bash
ssh safar@165.232.178.54
```

### Step 2: Set Environment Variables

```bash
# Set Brevo credentials
export BREVO_SMTP_USER="noreply@safarzonetravels.com"
export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

### Step 3: Make Permanent (So it survives server restart)

```bash
# Add to ~/.bashrc
echo 'export BREVO_SMTP_USER="noreply@safarzonetravels.com"' >> ~/.bashrc
echo 'export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Restart Your Application

```bash
# If using systemd
sudo systemctl restart gunicorn

# If using supervisor  
sudo supervisorctl restart gunicorn

# Or restart nginx
sudo systemctl restart nginx
```

### Step 5: Test

Try password reset again - it should work now!

## What I Fixed

✅ **Password reset function** - Now uses same fallback logic as OTP  
✅ **Brevo support** - Will try Brevo if GoDaddy fails  
✅ **Multiple fallbacks** - GoDaddy → Brevo → Gmail → Outlook  

## Expected Result

After setting credentials and restarting:
- Password reset emails will work
- OTP emails will work  
- Ticket emails will work

All will use Brevo if GoDaddy fails!

## Verify Credentials Are Set

```bash
# Check if variables are set
echo $BREVO_SMTP_USER
echo $BREVO_SMTP_KEY

# Should show:
# noreply@safarzonetravels.com
# xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV
```

## If Still Not Working

Check logs:
```bash
tail -f logs/email.log
```

You should see:
```
Trying Brevo-Port587: smtp-relay.brevo.com:587
✓ Password reset email sent successfully using Brevo-Port587
```

---

## Quick Copy-Paste Commands

```bash
# SSH to server
ssh safar@165.232.178.54

# Set credentials
export BREVO_SMTP_USER="noreply@safarzonetravels.com"
export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"

# Make permanent
echo 'export BREVO_SMTP_USER="noreply@safarzonetravels.com"' >> ~/.bashrc
echo 'export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"' >> ~/.bashrc
source ~/.bashrc

# Restart app
sudo systemctl restart gunicorn
```

**Done! Email should work now!** ✅

