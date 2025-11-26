#!/bin/bash
# ============================================
# Safar Zone Travels - Complete Auto Deployment
# GitHub: https://github.com/AbdurrabKhan198/travel-company.git
# Domain: safarzonetravels.com
# IP: 165.232.178.54
# ============================================
# Usage: bash deploy_on_server.sh
# ============================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Safar Zone Travels - Auto Deployment${NC}"
echo -e "${BLUE}  Domain: safarzonetravels.com${NC}"
echo -e "${BLUE}  IP: 165.232.178.54${NC}"
echo -e "${BLUE}============================================${NC}"
echo

# Configuration
PROJECT_DIR="/var/www/safarzonetravels"
GIT_REPO="https://github.com/AbdurrabKhan198/travel-company.git"
PROJECT_USER="safar"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${YELLOW}[INFO] Not running as root. Some commands will use sudo.${NC}"
    USE_SUDO="sudo"
else
    USE_SUDO=""
    echo -e "${GREEN}[INFO] Running as root.${NC}"
fi

echo -e "${BLUE}[1/10] Updating system packages...${NC}"
$USE_SUDO apt update -qq
$USE_SUDO apt upgrade -y -qq

echo
echo -e "${BLUE}[2/10] Installing required packages...${NC}"
$USE_SUDO apt install -y python3 python3-pip python3-venv python3-dev nginx postgresql postgresql-contrib libpq-dev build-essential libssl-dev libffi-dev git

echo
echo -e "${BLUE}[3/10] Creating project directory...${NC}"
$USE_SUDO mkdir -p $PROJECT_DIR
$USE_SUDO chown $PROJECT_USER:$PROJECT_USER $PROJECT_DIR

echo
echo -e "${BLUE}[4/10] Configuring firewall...${NC}"
$USE_SUDO ufw allow 'Nginx Full' 2>/dev/null || true
$USE_SUDO ufw allow OpenSSH 2>/dev/null || true
$USE_SUDO ufw --force enable 2>/dev/null || true

echo
echo -e "${BLUE}[5/10] Cloning/Updating repository from GitHub...${NC}"
if [ -d "$PROJECT_DIR/.git" ]; then
    echo -e "${YELLOW}[INFO] Repository exists. Pulling latest changes...${NC}"
    cd $PROJECT_DIR
    if [ "$EUID" -eq 0 ]; then
        sudo -u $PROJECT_USER git pull origin main || sudo -u $PROJECT_USER git pull origin master
    else
        git pull origin main || git pull origin master
    fi
else
    echo -e "${YELLOW}[INFO] Cloning repository...${NC}"
    cd /tmp
    rm -rf travel-company-temp 2>/dev/null || true
    git clone $GIT_REPO travel-company-temp
    cp -r travel-company-temp/* $PROJECT_DIR/ 2>/dev/null || true
    cp -r travel-company-temp/.* $PROJECT_DIR/ 2>/dev/null || true
    rm -rf travel-company-temp
    cd $PROJECT_DIR
    chown -R $PROJECT_USER:$PROJECT_USER $PROJECT_DIR
fi

echo
echo -e "${BLUE}[6/10] Setting up Python virtual environment...${NC}"
cd $PROJECT_DIR
if [ ! -d "venv" ]; then
    if [ "$EUID" -eq 0 ]; then
        sudo -u $PROJECT_USER python3 -m venv venv
    else
        python3 -m venv venv
    fi
    echo -e "${GREEN}[OK] Virtual environment created.${NC}"
else
    echo -e "${YELLOW}[INFO] Virtual environment already exists.${NC}"
fi

echo
echo -e "${BLUE}[7/10] Installing Python dependencies...${NC}"
if [ "$EUID" -eq 0 ]; then
    sudo -u $PROJECT_USER bash -c "cd $PROJECT_DIR && source venv/bin/activate && pip install --upgrade pip -q && pip install -r requirements.txt -q && echo '[OK] Dependencies installed.'"
else
    cd $PROJECT_DIR
    source venv/bin/activate
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo "[OK] Dependencies installed."
fi

echo
echo -e "${BLUE}[8/10] Configuring Django...${NC}"
if [ "$EUID" -eq 0 ]; then
    sudo -u $PROJECT_USER bash -c "cd $PROJECT_DIR && source venv/bin/activate && export DEBUG=False && export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54' && python manage.py migrate --noinput && python manage.py collectstatic --noinput --clear && echo '[OK] Django configured.'"
else
    cd $PROJECT_DIR
    source venv/bin/activate
    export DEBUG=False
    export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'
    python manage.py migrate --noinput
    python manage.py collectstatic --noinput --clear
    echo "[OK] Django configured."
fi

echo
echo -e "${BLUE}[9/10] Creating Gunicorn service...${NC}"
cat > /tmp/gunicorn.service << 'GUNICORN_EOF'
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

$USE_SUDO cp /tmp/gunicorn.service /etc/systemd/system/gunicorn.service
$USE_SUDO systemctl daemon-reload
$USE_SUDO systemctl start gunicorn
$USE_SUDO systemctl enable gunicorn

echo
echo -e "${BLUE}[10/10] Configuring Nginx...${NC}"
cat > /tmp/safarzonetravels << 'NGINX_EOF'
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

$USE_SUDO cp /tmp/safarzonetravels /etc/nginx/sites-available/safarzonetravels
$USE_SUDO ln -sf /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
$USE_SUDO rm -f /etc/nginx/sites-enabled/default
$USE_SUDO nginx -t
$USE_SUDO systemctl restart nginx

# Cleanup
rm -f /tmp/gunicorn.service /tmp/safarzonetravels

echo
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo
echo -e "${GREEN}Your website is now live at:${NC}"
echo -e "  ${BLUE}http://safarzonetravels.com${NC}"
echo -e "  ${BLUE}http://165.232.178.54${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Create superuser: cd /var/www/safarzonetravels && source venv/bin/activate && python manage.py createsuperuser"
echo "2. Setup SSL: sudo apt install -y certbot python3-certbot-nginx && sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com"
echo
echo -e "${GREEN}Check service status:${NC}"
echo "  sudo systemctl status gunicorn"
echo "  sudo systemctl status nginx"
echo
