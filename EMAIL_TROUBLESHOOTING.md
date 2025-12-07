# Email Troubleshooting Guide for DigitalOcean + GoDaddy

## Problem
Email/OTP functionality works locally but not on DigitalOcean production server.

## Common Causes
1. **DigitalOcean blocks outbound SMTP ports** (25, 587, 465) to prevent spam
2. **Firewall restrictions** on the server
3. **GoDaddy SMTP authentication issues**
4. **Network connectivity problems**

## Solution Implemented

### 1. Multiple SMTP Fallback Configurations
The system now tries multiple GoDaddy SMTP ports in order:
- **Port 80** (HTTP port - usually not blocked) - Primary for production
- **Port 3535** (GoDaddy alternative)
- **Port 25** (Standard SMTP)
- **Port 465** (SSL)
- **Port 587** (TLS)

### 2. Enhanced Logging
All email attempts are logged to:
- `logs/email.log` - File logging
- Console output (in development)

### 3. Environment Variables
You can override email settings using environment variables:
```bash
export EMAIL_HOST='smtpout.secureserver.net'
export EMAIL_PORT='80'
export EMAIL_USE_TLS='False'
export EMAIL_USE_SSL='False'
export EMAIL_HOST_USER='noreply@safarzonetravels.com'
export EMAIL_HOST_PASSWORD='your_password'
export DEFAULT_FROM_EMAIL='noreply@safarzonetravels.com'
```

## Testing on Server

### 1. Check if ports are accessible:
```bash
# Test port 80
telnet smtpout.secureserver.net 80

# Test port 3535
telnet smtpout.secureserver.net 3535

# Test port 25
telnet smtpout.secureserver.net 25
```

### 2. Check email logs:
```bash
tail -f logs/email.log
```

### 3. Test SMTP connection manually:
```python
# Run in Django shell: python manage.py shell
from django.core.mail import get_connection
from django.conf import settings

# Test port 80
conn = get_connection(
    host='smtpout.secureserver.net',
    port=80,
    username=settings.EMAIL_HOST_USER,
    password=settings.EMAIL_HOST_PASSWORD,
    use_tls=False,
    use_ssl=False,
    timeout=30,
)
conn.open()
print("Connection successful!")
conn.close()
```

## Alternative Solutions

### Option 1: Use GoDaddy Webmail API
If SMTP continues to fail, consider using GoDaddy's API instead.

### Option 2: Use Third-Party Email Service
- **SendGrid** (Free tier: 100 emails/day)
- **Mailgun** (Free tier: 5,000 emails/month)
- **Amazon SES** (Very cheap, reliable)
- **Postmark** (Great for transactional emails)

### Option 3: Request Port Unblock from DigitalOcean
Contact DigitalOcean support to unblock SMTP ports (they may require justification).

### Option 4: Use SMTP Relay Service
Use a service like Mailgun or SendGrid as an SMTP relay.

## Current Configuration

The system is configured to:
1. Try port 80 first (most likely to work on DigitalOcean)
2. Fall back to other ports automatically
3. Log all attempts for debugging
4. Return detailed error messages

## Next Steps

1. **Deploy the updated code** to your server
2. **Check the logs** (`logs/email.log`) after attempting to send an OTP
3. **Review the error messages** to see which port/configuration works
4. **If all fail**, consider switching to a third-party email service

## Quick Fix Commands

```bash
# On your DigitalOcean server, create logs directory
mkdir -p logs
chmod 755 logs

# Restart your Django application
# (depends on your deployment method - gunicorn, systemd, etc.)

# Monitor logs in real-time
tail -f logs/email.log
```

## Contact Information

If issues persist, check:
- GoDaddy email account is active
- Password is correct
- Email account is not locked/suspended
- Domain DNS settings are correct

