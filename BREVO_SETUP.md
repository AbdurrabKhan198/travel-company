# Brevo (Sendinblue) Setup Guide - FREE 300 emails/day

## ✅ Brevo Account Created!

Ab aapko Brevo se SMTP credentials chahiye. Ye steps follow karein:

## Step 1: Brevo se SMTP Credentials Lein

1. **Brevo Dashboard mein login karein:**
   - https://app.brevo.com/login

2. **SMTP Settings mein jayein:**
   - Left sidebar → **Settings** → **SMTP & API**
   - Ya direct: https://app.brevo.com/settings/smtp

3. **SMTP Credentials dekhein:**
   - **SMTP Server**: `smtp-relay.brevo.com`
   - **Port**: `587` (TLS) ya `465` (SSL)
   - **Login**: Aapka Brevo account email
   - **Password**: SMTP password (ye alag hai account password se)

4. **Agar SMTP password nahi hai:**
   - "Generate SMTP Key" button click karein
   - Password copy kar lein (ye sirf ek baar dikhega!)

## Step 2: Server par Environment Variables Set Karein

### Option A: Environment Variables (Recommended)

```bash
# Server par SSH karein aur ye commands run karein:
export BREVO_SMTP_USER="your-email@example.com"  # Aapka Brevo account email
export BREVO_SMTP_KEY="your-smtp-password"       # Brevo SMTP password
```

### Option B: .env File mein Add Karein

`.env` file create/update karein:
```
BREVO_SMTP_USER=your-email@example.com
BREVO_SMTP_KEY=your-smtp-password
```

### Option C: settings.py mein Direct (Temporary - Testing ke liye)

```python
# settings.py mein add karein (testing ke liye)
BREVO_SMTP_USER = 'your-email@example.com'
BREVO_SMTP_KEY = 'your-smtp-password'
```

**⚠️ Important:** Production mein `.env` file ya environment variables use karein, settings.py mein direct mat likhein!

## Step 3: Deploy aur Test Karein

1. **Code deploy karein**
2. **OTP send karke test karein**
3. **Logs check karein**: `tail -f logs/email.log`

## Expected Result

Agar sab sahi hai, logs mein dikhega:
```
✓ Email sent successfully using Brevo-Port587
```

## Brevo SMTP Details

- **SMTP Server**: `smtp-relay.brevo.com`
- **Port 587**: TLS (Recommended)
- **Port 465**: SSL (Alternative)
- **Username**: Aapka Brevo account email
- **Password**: Brevo SMTP password (account password nahi!)

## Free Tier Limits

✅ **300 emails/day** - FREE forever  
✅ **No credit card required**  
✅ **Works on DigitalOcean**  
✅ **No port blocking issues**  

## Priority Order

Code automatically try karega:
1. **GoDaddy port 2525** (first)
2. **Brevo** (if GoDaddy fails) ← **Yeh ab try hoga!**
3. **Gmail** (if Brevo fails)
4. **Outlook** (if Gmail fails)

## Troubleshooting

### Issue: "Authentication failed"
- **Solution**: Check karein SMTP password sahi hai ya nahi
- Brevo dashboard se new SMTP key generate karein

### Issue: "Connection timeout"
- **Solution**: Port 465 try karega automatically
- Firewall check karein

### Issue: "Email not received"
- **Solution**: Brevo dashboard → **Statistics** → Check email status
- Spam folder check karein

## Brevo Dashboard Links

- **Login**: https://app.brevo.com/login
- **SMTP Settings**: https://app.brevo.com/settings/smtp
- **Email Statistics**: https://app.brevo.com/statistics
- **Support**: https://help.brevo.com/

## Quick Test

Server par ye command run karein:
```bash
python manage.py shell
```

Phir:
```python
from django.core.mail import send_mail
from django.conf import settings

send_mail(
    'Test Email',
    'This is a test from Brevo',
    settings.DEFAULT_FROM_EMAIL,
    ['your-email@gmail.com'],
    fail_silently=False,
)
```

Agar email aaye → **Working!** ✅

## Client ko Kya Batayein?

"Email service Brevo se setup kar di hai - completely free, 300 emails per day. Koi extra charges nahi."

---

## Next Steps

1. ✅ Brevo account created
2. ⏳ SMTP credentials lein
3. ⏳ Server par environment variables set karein
4. ⏳ Deploy aur test karein

**Brevo credentials milte hi setup ho jayega!** 🚀

