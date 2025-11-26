# Safar Zone Travels - Server Deployment Steps

## Domain: safarzonetravels.com
## IP: 165.232.178.54
## GitHub: https://github.com/AbdurrabKhan198/travel-company.git

---

## ✅ Completed Steps (You've already done these)

1. ✅ SSH into server: `ssh root@165.232.178.54`
2. ✅ Created user: `adduser safar`
3. ✅ Added to sudo: `usermod -aG sudo safar`
4. ✅ Configured firewall: `ufw allow OpenSSH` and `ufw enable`

---

## 📋 Next Steps to Complete Deployment

### Step 1: Run Server Setup Script (as root)

```bash
# Upload deploy_server.sh to server, then:
chmod +x deploy_server.sh
sudo ./deploy_server.sh
```

**OR manually run these commands:**

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and packages
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install Nginx
sudo apt install -y nginx

# Install PostgreSQL (optional)
sudo apt install -y postgresql postgresql-contrib libpq-dev

# Install build tools
sudo apt install -y build-essential libssl-dev libffi-dev

# Create project directory
sudo mkdir -p /var/www/safarzonetravels
sudo chown safar:safar /var/www/safarzonetravels

# Configure firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
```

---

### Step 2: Switch to 'safar' User and Clone from GitHub

```bash
# Switch to safar user
su - safar

# Navigate to project directory
cd /var/www/safarzonetravels

# Install Git if not already installed
sudo apt install -y git

# Clone your repository
git clone https://github.com/AbdurrabKhan198/travel-company.git .

# Or if directory is not empty, clone to temp and move files
# git clone https://github.com/AbdurrabKhan198/travel-company.git /tmp/travel-company
# cp -r /tmp/travel-company/* /var/www/safarzonetravels/
# cp -r /tmp/travel-company/.* /var/www/safarzonetravels/ 2>/dev/null || true
```

**Note:** Make sure your GitHub repository is up to date with all your latest code!

---

### Step 3: Setup Python Virtual Environment

```bash
# Make sure you're in /var/www/safarzonetravels
cd /var/www/safarzonetravels

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

### Step 4: Configure Django Settings

```bash
# Set environment variables (add to ~/.bashrc for persistence)
export DEBUG=False
export SECRET_KEY='your-secret-key-here'  # Generate a new one!
export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'

# Or create .env file (if using python-decouple)
# Install: pip install python-decouple
```

**Generate a new SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### Step 5: Database Setup

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

---

### Step 6: Create Gunicorn Service

```bash
# Switch back to root
exit  # or use sudo

# Create service file
sudo nano /etc/systemd/system/gunicorn.service
```

**Paste this content:**

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

[Install]
WantedBy=multi-user.target
```

**Save and exit (Ctrl+X, Y, Enter)**

**Start Gunicorn:**
```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

### Step 7: Configure Nginx

```bash
# Create Nginx config
sudo nano /etc/nginx/sites-available/safarzonetravels
```

**Paste this content:**

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

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

### Step 8: Setup SSL Certificate (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

### Step 9: Verify Everything Works

```bash
# Check Gunicorn status
sudo systemctl status gunicorn

# Check Nginx status
sudo systemctl status nginx

# Check logs if needed
sudo journalctl -u gunicorn -f
sudo tail -f /var/log/nginx/error.log
```

**Test in browser:**
- http://safarzonetravels.com
- http://165.232.178.54
- https://safarzonetravels.com (after SSL setup)

---

## 🔧 Useful Commands

### Restart Services
```bash
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Check Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

### Update Code
```bash
cd /var/www/safarzonetravels
source venv/bin/activate
# Upload new files or git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

---

## ⚠️ Important Notes

1. **DNS Configuration**: Make sure your domain DNS points to `165.232.178.54`
   - A Record: `@` → `165.232.178.54`
   - A Record: `www` → `165.232.178.54`

2. **SECRET_KEY**: Generate a new secret key for production! Don't use the default one.

3. **Database**: Currently using SQLite. For production, consider PostgreSQL.

4. **File Permissions**: Make sure `/var/www/safarzonetravels` is owned by `safar` user.

5. **Firewall**: Ports 80 and 443 should be open.

---

## 🆘 Troubleshooting

### Gunicorn won't start
```bash
sudo journalctl -u gunicorn -n 50
# Check file permissions and paths
```

### Nginx 502 Bad Gateway
```bash
# Check if Gunicorn is running
sudo systemctl status gunicorn
# Check socket permissions
ls -la /var/www/safarzonetravels/gunicorn.sock
```

### Static files not loading
```bash
# Recollect static files
python manage.py collectstatic --noinput --clear
# Check Nginx config
sudo nginx -t
```

---

## ✅ Deployment Checklist

- [ ] Server packages installed
- [ ] Project files uploaded
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Database migrated
- [ ] Static files collected
- [ ] Superuser created
- [ ] Gunicorn service running
- [ ] Nginx configured and running
- [ ] SSL certificate installed
- [ ] DNS configured
- [ ] Firewall configured
- [ ] Site accessible via domain

---

**Need help?** Check the logs and verify each step was completed successfully.

