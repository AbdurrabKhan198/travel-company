# 🚀 SendGrid Setup Guide (FREE - 100 emails/day)

## Why SendGrid?
- ✅ **FREE** - 100 emails per day (perfect for OTPs and tickets)
- ✅ **Works on DigitalOcean** - No port blocking issues
- ✅ **Reliable** - Used by thousands of companies
- ✅ **Easy Setup** - Just need an API key

## Step 1: Sign Up for SendGrid (FREE)

1. Go to: **https://signup.sendgrid.com/**
2. Sign up with your email (use your business email)
3. Verify your email address
4. Complete the account setup

## Step 2: Create API Key

1. Login to SendGrid dashboard: **https://app.sendgrid.com/**
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Name it: `SafarZone Travels`
5. Select **Full Access** (or **Restricted Access** with Mail Send permissions)
6. Click **Create & View**
7. **COPY THE API KEY** - You'll only see it once!

## Step 3: Verify Sender Email (Important!)

1. Go to **Settings** → **Sender Authentication**
2. Click **Verify a Single Sender**
3. Fill in the form:
   - **From Email**: `noreply@safarzonetravels.com`
   - **From Name**: `Safar Zone Travels`
   - **Reply To**: `support@safarzonetravels.com`
   - **Company Address**: Your business address
   - **Website URL**: `https://safarzonetravels.com`
4. Click **Create**
5. **Check your email** and click the verification link

## Step 4: Set Environment Variable on Server

### Option A: Set in Server Environment (Recommended)

```bash
# SSH to your server
ssh safar@165.232.178.54

# Add to ~/.bashrc or ~/.profile
echo 'export SENDGRID_API_KEY="YOUR_API_KEY_HERE"' >> ~/.bashrc
source ~/.bashrc

# Or set it for the current session
export SENDGRID_API_KEY="YOUR_API_KEY_HERE"
```

### Option B: Set in Django Settings (Temporary - for testing)

Edit `Travel_agency/settings.py` and add:

```python
SENDGRID_API_KEY = 'YOUR_API_KEY_HERE'  # Replace with your actual key
```

**⚠️ IMPORTANT:** Remove this after testing and use environment variables instead!

## Step 5: Install SendGrid Package

```bash
# On your server
cd /var/www/safarzonetravels
source venv/bin/activate
pip install sendgrid>=6.10.0
```

Or if you have `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Step 6: Restart Your Application

```bash
# If using systemd
sudo systemctl restart gunicorn

# If using supervisor
sudo supervisorctl restart gunicorn

# Or restart your web server
sudo systemctl restart nginx
```

## Step 7: Test It!

1. Try sending an OTP from your website
2. Check the logs: `tail -f logs/email.log`
3. You should see: `✓ Email sent successfully using SendGrid`

## Troubleshooting

### Issue: "Authentication failed"
- **Solution**: Make sure your API key is correct and has Mail Send permissions

### Issue: "Sender not verified"
- **Solution**: Complete Step 3 above - verify your sender email

### Issue: "Rate limit exceeded"
- **Solution**: You've hit the 100 emails/day limit. Wait 24 hours or upgrade to paid plan

### Issue: Still not working?
- Check logs: `tail -f logs/email.log`
- Verify API key is set: `echo $SENDGRID_API_KEY`
- Test connection manually (see below)

## Manual Testing

```python
# Run in Django shell: python manage.py shell
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test email from SendGrid',
    'noreply@safarzonetravels.com',
    ['your-email@gmail.com'],
    fail_silently=False,
)
```

## Cost

- **FREE**: 100 emails/day forever
- **Essentials Plan**: $19.95/month for 50,000 emails
- **Pro Plan**: $89.95/month for 100,000 emails

For a travel booking site, 100 emails/day is usually enough for OTPs and ticket emails.

## Your GoDaddy Email is NOT Wasted!

- You can still use it for:
  - Personal/business emails
  - Customer support emails
  - Backup email service
  - Other applications

The system will automatically use SendGrid if configured, and fallback to GoDaddy if SendGrid fails.

## Need Help?

- SendGrid Support: https://support.sendgrid.com/
- Documentation: https://docs.sendgrid.com/
- Status Page: https://status.sendgrid.com/

