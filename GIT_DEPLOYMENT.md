# Git-based Deployment Guide

## GitHub Repository
**Repository:** https://github.com/AbdurrabKhan198/travel-company.git

## Domain & Server
- **Domain:** safarzonetravels.com
- **IP:** 165.232.178.54

---

## 🚀 Quick Deployment (Recommended)

### Step 1: Initial Server Setup (Run ONCE as root)

```bash
# SSH to server
ssh root@165.232.178.54

# Upload initial_server_setup.sh and run it
chmod +x initial_server_setup.sh
sudo ./initial_server_setup.sh
```

This will:
- Install all required packages
- Create project directory
- Configure firewall
- Set up Gunicorn service
- Configure Nginx

### Step 2: Deploy from GitHub (Run as safar user)

```bash
# Switch to safar user
su - safar

# Navigate to project directory
cd /var/www/safarzonetravels

# Upload deploy_with_git.sh and run it
chmod +x deploy_with_git.sh
bash deploy_with_git.sh
```

This will:
- Clone/pull from GitHub
- Create virtual environment
- Install dependencies
- Run migrations
- Collect static files
- Restart services

---

## 📝 Manual Deployment Steps

### 1. Prepare Server (as root)

```bash
# Install packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib libpq-dev build-essential libssl-dev libffi-dev git

# Create project directory
sudo mkdir -p /var/www/safarzonetravels
sudo chown safar:safar /var/www/safarzonetravels

# Configure firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw enable
```

### 2. Clone Repository (as safar user)

```bash
# Switch to safar user
su - safar

# Navigate to project directory
cd /var/www/safarzonetravels

# Clone repository
git clone https://github.com/AbdurrabKhan198/travel-company.git .
```

### 3. Setup Python Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Django

```bash
# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Set environment variables (add to ~/.bashrc for persistence)
export DEBUG=False
export SECRET_KEY='your-generated-secret-key-here'
export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 5. Setup Gunicorn Service (as root)

```bash
# Create service file
sudo nano /etc/systemd/system/gunicorn.service
```

Paste:
```ini
[Unit]
Description=gunicorn daemon for Safar Zone Travels
After=network.target

[Service]
User=safar
Group=safar
WorkingDirectory=/var/www/safarzonetravels
ExecStart=/var/www/safarzonetravels/venv/bin/gunicorn \
    --workers 4 \
    --timeout 120 \
    --bind unix:/var/www/safarzonetravels/gunicorn.sock \
    Travel_agency.wsgi:application
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

### 6. Configure Nginx (as root)

```bash
# Create config
sudo nano /etc/nginx/sites-available/safarzonetravels
```

Paste:
```nginx
server {
    listen 80;
    server_name safarzonetravels.com www.safarzonetravels.com 165.232.178.54;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/safarzonetravels/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/safarzonetravels/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/var/www/safarzonetravels/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }
}
```

Enable and restart:
```bash
sudo ln -s /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### 7. Setup SSL Certificate

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🔄 Updating Your Site

### Method 1: Using Deployment Script (Recommended)

```bash
# As safar user
cd /var/www/safarzonetravels
bash deploy_with_git.sh
```

### Method 2: Manual Update

```bash
# As safar user
cd /var/www/safarzonetravels
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## 📋 Workflow

### On Your Local Machine (Windows)

1. **Make changes to your code**
2. **Commit changes:**
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

### On Server

1. **Pull latest changes:**
   ```bash
   cd /var/www/safarzonetravels
   bash deploy_with_git.sh
   ```

That's it! Your site will be updated automatically.

---

## 🔧 Troubleshooting

### Git Authentication Issues

If you need to use private repository or have authentication issues:

```bash
# Setup SSH key
ssh-keygen -t ed25519 -C "your_email@example.com"
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub: Settings > SSH and GPG keys

# Clone using SSH
git clone git@github.com:AbdurrabKhan198/travel-company.git .
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R safar:safar /var/www/safarzonetravels

# Fix permissions
sudo chmod -R 755 /var/www/safarzonetravels
```

### Service Issues

```bash
# Check Gunicorn status
sudo systemctl status gunicorn
sudo journalctl -u gunicorn -f

# Check Nginx status
sudo systemctl status nginx
sudo nginx -t
```

---

## ✅ Checklist

- [ ] Server packages installed
- [ ] Repository cloned from GitHub
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database migrated
- [ ] Static files collected
- [ ] Superuser created
- [ ] Gunicorn service running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] DNS configured
- [ ] Site accessible via domain

---

## 🎯 Quick Commands Reference

```bash
# Deploy/Update
cd /var/www/safarzonetravels && bash deploy_with_git.sh

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx

# View logs
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

---

**Your GitHub Repository:** https://github.com/AbdurrabKhan198/travel-company.git

