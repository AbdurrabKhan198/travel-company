# ⚡ IMMEDIATE FIX - Brevo Credentials Added to Settings

## ✅ What I Did

Added Brevo credentials directly to `settings.py` so emails work **immediately** without needing to set environment variables.

## 🚀 Deploy Now

1. **Commit and push:**
   ```bash
   git add Travel_agency/settings.py
   git commit -m "Add Brevo credentials for immediate email fix"
   git push origin main
   ```

2. **Deploy to server:**
   ```bash
   # On server
   cd /var/www/safarzonetravels
   git pull origin main
   sudo systemctl restart gunicorn
   ```

3. **Test:**
   - Try signup OTP
   - Should work now!

## Expected Logs

After deploy, you should see:
```
Trying GoDaddy-smtpout-Port2525-TLS: smtpout.secureserver.net:2525
✗ Failed with GoDaddy-smtpout-Port2525-TLS: timed out
Trying Brevo-Port587: smtp-relay.brevo.com:587
✓ Email sent successfully using Brevo-Port587
```

## ⚠️ Security Note

**For production security**, later move these to environment variables:

```bash
# On server - set in systemd service file
Environment="BREVO_SMTP_USER=noreply@safarzonetravels.com"
Environment="BREVO_SMTP_KEY=xsmtpsib-..."
```

But for now, this will get emails working immediately!

---

## Quick Deploy Commands

```bash
# On your local machine
git add Travel_agency/settings.py
git commit -m "Add Brevo credentials - immediate fix"
git push origin main

# On server (SSH)
ssh safar@165.232.178.54
cd /var/www/safarzonetravels
git pull origin main
sudo systemctl restart gunicorn
tail -f logs/email.log
```

**Emails will work after this!** ✅

