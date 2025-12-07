# Server Setup - Brevo Credentials

## ⚠️ IMPORTANT: Set These on Your Server

Brevo credentials are NOT in code (for security). You MUST set them as environment variables on your server.

## Step 1: SSH to Your Server

```bash
ssh safar@165.232.178.54
```

## Step 2: Set Environment Variables

### Option A: Temporary (Current Session Only)

```bash
export BREVO_SMTP_USER="noreply@safarzonetravels.com"
export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"
```

### Option B: Permanent (Recommended)

Add to `~/.bashrc` or `~/.profile`:

```bash
echo 'export BREVO_SMTP_USER="noreply@safarzonetravels.com"' >> ~/.bashrc
echo 'export BREVO_SMTP_KEY="xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV"' >> ~/.bashrc
source ~/.bashrc
```

### Option C: .env File (If Using)

Create `.env` file in project root:

```bash
cd /var/www/safarzonetravels
nano .env
```

Add:
```
BREVO_SMTP_USER=noreply@safarzonetravels.com
BREVO_SMTP_KEY=xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV
```

## Step 3: Restart Your Application

```bash
# If using systemd
sudo systemctl restart gunicorn

# If using supervisor
sudo supervisorctl restart gunicorn

# Or restart your web server
sudo systemctl restart nginx
```

## Step 4: Test

```bash
# Check if variables are set
echo $BREVO_SMTP_USER
echo $BREVO_SMTP_KEY

# Test email sending
python manage.py shell
```

Then in shell:
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

## Your Brevo Credentials

- **Email**: noreply@safarzonetravels.com
- **SMTP Key**: xsmtpsib-6b0398d2fc0edcd5bd53acd551bfe6c56ec94d70b507bc22d1bb02075cb0681c-vmKQQ32EtVYZ6poV

**⚠️ Never commit these to git!**

