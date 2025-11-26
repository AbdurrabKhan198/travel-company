@echo off
chcp 65001 >nul
title Safar Zone Travels - Auto Deployment
color 0A
cls

REM ============================================
REM Safar Zone Travels - Complete Auto Deployment
REM GitHub: https://github.com/AbdurrabKhan198/travel-company.git
REM Domain: safarzonetravels.com
REM IP: 165.232.178.54
REM ============================================

echo.
echo ============================================
echo   Safar Zone Travels - Auto Deployment
echo   Domain: safarzonetravels.com
echo   IP: 165.232.178.54
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0"

echo [STEP 1/5] Checking prerequisites...
echo.

REM Check if SSH is available
where ssh >nul 2>&1
if errorlevel 1 (
    echo [ERROR] SSH not found!
    echo.
    echo Please install one of these:
    echo 1. Git for Windows (includes SSH)
    echo 2. OpenSSH for Windows
    echo.
    echo Download Git: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo [OK] SSH found
echo.

REM Get server credentials
echo [STEP 2/5] Server Connection Setup
echo.
set /p SERVER_USER="Enter server username (default: root): "
if "%SERVER_USER%"=="" set SERVER_USER=root
set SERVER_IP=165.232.178.54
set PROJECT_USER=safar

echo.
echo Connecting to: %SERVER_USER%@%SERVER_IP%
echo.

REM Create deployment script on server
echo [STEP 3/5] Creating deployment script on server...
echo.

ssh %SERVER_USER%@%SERVER_IP% "bash -s" << 'DEPLOY_SCRIPT'
#!/bin/bash
set -e

echo "============================================"
echo "  Safar Zone Travels - Auto Deployment"
echo "============================================"
echo

# Step 1: Install packages (as root)
echo "[1/8] Installing packages..."
apt update -qq
apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib libpq-dev build-essential libssl-dev libffi-dev git

# Step 2: Create project directory
echo "[2/8] Creating project directory..."
mkdir -p /var/www/safarzonetravels
chown safar:safar /var/www/safarzonetravels

# Step 3: Configure firewall
echo "[3/8] Configuring firewall..."
ufw allow 'Nginx Full' 2>/dev/null || true
ufw allow OpenSSH 2>/dev/null || true
ufw --force enable 2>/dev/null || true

# Step 4: Create Gunicorn service
echo "[4/8] Creating Gunicorn service..."
cat > /etc/systemd/system/gunicorn.service << 'GUNICORN_EOF'
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
GUNICORN_EOF

# Step 5: Create Nginx config
echo "[5/8] Creating Nginx configuration..."
cat > /etc/nginx/sites-available/safarzonetravels << 'NGINX_EOF'
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
NGINX_EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx
nginx -t

# Reload systemd
systemctl daemon-reload

echo "[6/8] Server setup complete!"
echo

# Step 6: Switch to safar user and deploy
echo "[7/8] Deploying application from GitHub..."
sudo -u safar bash << 'DEPLOY_APP'
#!/bin/bash
set -e

cd /var/www/safarzonetravels

# Clone repository
if [ -d ".git" ]; then
    echo "Repository exists. Pulling latest changes..."
    git pull origin main || git pull origin master
else
    echo "Cloning repository from GitHub..."
    git clone https://github.com/AbdurrabKhan198/travel-company.git .
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

# Set environment variables
export DEBUG=False
export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Application deployment complete!"
DEPLOY_APP

# Step 7: Start services
echo "[8/8] Starting services..."
systemctl start gunicorn
systemctl enable gunicorn
systemctl restart nginx

echo
echo "============================================"
echo "  Deployment Complete!"
echo "============================================"
echo
echo "Your site should be live at:"
echo "  http://safarzonetravels.com"
echo "  http://165.232.178.54"
echo
echo "Next step: Setup SSL certificate"
echo "Run: certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com"
echo
DEPLOY_SCRIPT

if errorlevel 1 (
    echo.
    echo [ERROR] Deployment failed!
    echo.
    echo Please check:
    echo 1. SSH connection is working
    echo 2. You have root access
    echo 3. Internet connection is stable
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SUCCESS! Deployment Complete!
echo ============================================
echo.
echo Your website is now live at:
echo   http://safarzonetravels.com
echo   http://165.232.178.54
echo.
echo Next steps:
echo 1. Setup SSL: ssh root@165.232.178.54 "certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com"
echo 2. Create superuser: ssh safar@165.232.178.54 "cd /var/www/safarzonetravels && source venv/bin/activate && python manage.py createsuperuser"
echo.
pause

