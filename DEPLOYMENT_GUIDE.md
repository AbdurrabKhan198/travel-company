# Safar Zone Travels - DigitalOcean Deployment Guide

## Domain & Server Information
- **Domain**: safarzonetravels.com
- **IP Address**: 165.232.178.54
- **Server**: DigitalOcean Droplet

## Quick Start (Windows - One Click Deployment)

### Option 1: Using Batch Files (Recommended for Windows)

1. **Prepare for Deployment**
   ```batch
   Double-click: deploy.bat
   ```
   This will:
   - Install dependencies
   - Run migrations
   - Collect static files
   - Prepare the server

2. **Start Production Server**
   ```batch
   Double-click: production_start.bat
   ```
   This will start Gunicorn server on port 8000

## Manual Deployment Steps (Linux/DigitalOcean)

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and pip
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y

# Install PostgreSQL (optional, if not using SQLite)
sudo apt install postgresql postgresql-contrib -y
```

### 2. Upload Project Files

```bash
# Create project directory
sudo mkdir -p /var/www/safarzonetravels
sudo chown $USER:$USER /var/www/safarzonetravels

# Upload your project files to /var/www/safarzonetravels
# Or clone from Git repository
```

### 3. Setup Virtual Environment

```bash
cd /var/www/safarzonetravels
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure Django Settings

The settings.py is already configured with:
- Domain: safarzonetravels.com
- IP: 165.232.178.54
- Production security settings

### 5. Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 6. Configure Gunicorn

Create `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=gunicorn daemon for Safar Zone Travels
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/safarzonetravels
ExecStart=/var/www/safarzonetravels/venv/bin/gunicorn \
    --workers 4 \
    --timeout 120 \
    --bind unix:/var/www/safarzonetravels/gunicorn.sock \
    Travel_agency.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start Gunicorn:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

### 7. Configure Nginx

Create `/etc/nginx/sites-available/safarzonetravels`:

```nginx
server {
    listen 80;
    server_name safarzonetravels.com www.safarzonetravels.com 165.232.178.54;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/safarzonetravels/staticfiles/;
    }

    location /media/ {
        alias /var/www/safarzonetravels/media/;
    }

    location / {
        proxy_pass http://unix:/var/www/safarzonetravels/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Setup SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate
sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com

# Auto-renewal
sudo certbot renew --dry-run
```

### 9. Configure Firewall

```bash
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

### 10. DNS Configuration

Point your domain to the server IP:
- **A Record**: @ → 165.232.178.54
- **A Record**: www → 165.232.178.54

## Environment Variables

For production, set these environment variables:

```bash
export DEBUG=False
export SECRET_KEY='your-secret-key-here'
export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'
```

Or create a `.env` file and use `python-decouple` package.

## Troubleshooting

### Check Gunicorn Status
```bash
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f
```

### Check Nginx Status
```bash
sudo systemctl status nginx
sudo nginx -t
```

### Check Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Django logs
tail -f /var/www/safarzonetravels/logs/django.log
```

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Security Checklist

- [x] DEBUG = False in production
- [x] ALLOWED_HOSTS configured
- [x] SSL/HTTPS enabled
- [x] SECRET_KEY from environment variable
- [x] Security middleware enabled
- [x] CSRF and Session cookies secure
- [x] HSTS enabled
- [x] Firewall configured

## Maintenance Commands

```bash
# Update code
cd /var/www/safarzonetravels
source venv/bin/activate
git pull  # or upload new files
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

## Support

For issues, check:
- Django logs: `/var/www/safarzonetravels/logs/`
- Gunicorn logs: `sudo journalctl -u gunicorn`
- Nginx logs: `/var/log/nginx/`

