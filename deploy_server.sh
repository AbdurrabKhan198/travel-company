#!/bin/bash
# ============================================
# Safar Zone Travels - Server Deployment Script
# Domain: safarzonetravels.com
# IP: 165.232.178.54
# ============================================

set -e  # Exit on error

echo "============================================"
echo "  Safar Zone Travels - Server Deployment"
echo "  Domain: safarzonetravels.com"
echo "  IP: 165.232.178.54"
echo "============================================"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root or with sudo${NC}"
    exit 1
fi

echo "[1/10] Updating system packages..."
apt update && apt upgrade -y

echo
echo "[2/10] Installing Python and required packages..."
apt install -y python3 python3-pip python3-venv python3-dev

echo
echo "[3/10] Installing Nginx..."
apt install -y nginx

echo
echo "[4/10] Installing PostgreSQL (optional - for production database)..."
apt install -y postgresql postgresql-contrib libpq-dev

echo
echo "[5/10] Installing other dependencies..."
apt install -y build-essential libssl-dev libffi-dev

echo
echo "[6/10] Creating project directory..."
mkdir -p /var/www/safarzonetravels
chown safar:safar /var/www/safarzonetravels

echo
echo "[7/10] Setting up firewall rules..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo
echo "[8/10] Creating Gunicorn service file..."
cat > /etc/systemd/system/gunicorn.service << 'EOF'
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
EOF

echo
echo "[9/10] Creating Nginx configuration..."
cat > /etc/nginx/sites-available/safarzonetravels << 'EOF'
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
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo
echo "[10/10] Testing Nginx configuration..."
nginx -t

echo
echo -e "${GREEN}============================================"
echo "  Server Setup Complete!"
echo "============================================${NC}"
echo
echo "Next steps:"
echo "1. Switch to 'safar' user: su - safar"
echo "2. Upload your project files to /var/www/safarzonetravels"
echo "3. Create virtual environment: python3 -m venv venv"
echo "4. Activate venv: source venv/bin/activate"
echo "5. Install dependencies: pip install -r requirements.txt"
echo "6. Run migrations: python manage.py migrate"
echo "7. Collect static files: python manage.py collectstatic"
echo "8. Create superuser: python manage.py createsuperuser"
echo "9. Start services:"
echo "   sudo systemctl start gunicorn"
echo "   sudo systemctl enable gunicorn"
echo "   sudo systemctl restart nginx"
echo "10. Setup SSL: sudo certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com"
echo

