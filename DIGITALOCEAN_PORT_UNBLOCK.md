# DigitalOcean SMTP Port Blocking - Solution

## Problem
All GoDaddy SMTP ports are timing out. This means **DigitalOcean is blocking ALL outbound SMTP ports** on your server.

## Solution: Request Port Unblock (FREE)

DigitalOcean blocks SMTP ports by default to prevent spam, but they will unblock them for legitimate business use (like your travel booking system).

### Step 1: Contact DigitalOcean Support

1. **Login to DigitalOcean**: https://cloud.digitalocean.com/
2. **Go to Support**: Click "Support" in the top menu
3. **Create a Support Ticket**: Click "Create Ticket"
4. **Select**: "Technical" → "Networking"

### Step 2: Use This Template Message

```
Subject: Request to Unblock SMTP Ports for Business Email

Hello,

I need to unblock outbound SMTP ports on my Droplet (IP: 165.232.178.54) 
to send transactional emails from my travel booking application.

I am using GoDaddy Business Email (safarzonetravels.com) and need to send:
- OTP verification emails for user registration
- Booking confirmation emails
- Password reset emails

This is for legitimate business use only. I have purchased email services 
from GoDaddy and need to use their SMTP servers.

Please unblock the following ports for outbound SMTP:
- Port 25
- Port 465
- Port 587
- Port 2525
- Port 3535

Server IP: 165.232.178.54
Domain: safarzonetravels.com
Email Service: GoDaddy Business Email

Thank you!
```

### Step 3: Wait for Response

- DigitalOcean usually responds within 24 hours
- They will unblock the ports for your specific server
- **This is FREE** - no charges

### Step 4: Test After Unblock

Once ports are unblocked, test again:

```bash
# On your server
tail -f logs/email.log
```

Then try sending an OTP from your website. You should see:
```
✓ Email sent successfully using GoDaddy-smtpout-Port587-TLS
```

## Alternative: Check Firewall Rules

If DigitalOcean support says ports are not blocked, check your server's firewall:

```bash
# Check if UFW is blocking ports
sudo ufw status

# If UFW is active, allow outbound SMTP
sudo ufw allow out 25/tcp
sudo ufw allow out 465/tcp
sudo ufw allow out 587/tcp
sudo ufw allow out 2525/tcp
sudo ufw allow out 3535/tcp
```

## Why This Happens

- Cloud providers block SMTP ports by default to prevent spam
- This is a security measure
- They will unblock for legitimate business use
- **It's FREE** - just need to request it

## Timeline

- **Request sent**: Today
- **Response expected**: Within 24 hours
- **Ports unblocked**: Usually same day
- **Total cost**: $0 (FREE)

## After Ports Are Unblocked

Your GoDaddy email will work immediately. The system is already configured to try all ports automatically, so once DigitalOcean unblocks them, emails will start working.

## If DigitalOcean Refuses

If DigitalOcean refuses to unblock (rare), you have these options:

1. **Use GoDaddy Webmail API** (if available) - Check GoDaddy support
2. **Use a different cloud provider** that doesn't block SMTP
3. **Use a mail relay service** (but you said no extra charges)

But 99% of the time, DigitalOcean will unblock the ports for legitimate business use.

