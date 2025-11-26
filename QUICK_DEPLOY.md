# 🚀 Quick Deployment Guide - Using GitHub

## Your Repository
**GitHub:** https://github.com/AbdurrabKhan198/travel-company.git

## Server Info
- **Domain:** safarzonetravels.com
- **IP:** 165.232.178.54
- **User:** safar

---

## ⚡ Fastest Way to Deploy

### Step 1: Push Your Code to GitHub (On Windows)

```bash
# In your project directory
cd "C:\Users\hp\Desktop\clients\travel company\Travel_agency"

# Initialize git if not already done
git init
git add .
git commit -m "Initial deployment setup"

# Add remote (if not already added)
git remote add origin https://github.com/AbdurrabKhan198/travel-company.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 2: Initial Server Setup (Run ONCE on server as root)

```bash
# SSH to server
ssh root@165.232.178.54

# Upload initial_server_setup.sh to server, then:
chmod +x initial_server_setup.sh
sudo ./initial_server_setup.sh
```

**OR run manually:**
```bash
# Install packages
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib libpq-dev build-essential libssl-dev libffi-dev git

# Create directory
sudo mkdir -p /var/www/safarzonetravels
sudo chown safar:safar /var/www/safarzonetravels

# Configure firewall
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
```

### Step 3: Deploy from GitHub (Run as safar user)

```bash
# Switch to safar user
su - safar

# Navigate to project
cd /var/www/safarzonetravels

# Upload deploy_with_git.sh to server, then:
chmod +x deploy_with_git.sh
bash deploy_with_git.sh
```

**OR clone manually:**
```bash
# Clone repository
git clone https://github.com/AbdurrabKhan198/travel-company.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Setup Django
export DEBUG=False
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### Step 4: Setup Services (as root)

**Gunicorn Service:**
```bash
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

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

**Nginx Config:**
```bash
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

```bash
sudo ln -s /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Step 5: Setup SSL

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com
```

---

## 🔄 Updating Your Site (After Initial Setup)

### On Windows (Make Changes):
```bash
git add .
git commit -m "Your changes"
git push origin main
```

### On Server (Deploy Updates):
```bash
cd /var/www/safarzonetravels
bash deploy_with_git.sh
```

That's it! 🎉

---

## 📝 Important Notes

1. **Make sure your code is pushed to GitHub first**
2. **Run initial setup only once**
3. **Use deploy_with_git.sh for all future updates**
4. **Keep your SECRET_KEY secure - don't commit it to GitHub**

---

## 🆘 Need Help?

- Check `GIT_DEPLOYMENT.md` for detailed guide
- Check `SERVER_DEPLOYMENT_STEPS.md` for step-by-step instructions
- View logs: `sudo journalctl -u gunicorn -f`

