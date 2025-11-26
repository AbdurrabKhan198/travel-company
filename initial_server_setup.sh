#!/bin/bash
# ============================================
# Safar Zone Travels - Initial Server Setup
# Run this ONCE as root to prepare the server
# ============================================

set -e

echo "============================================"
echo "  Initial Server Setup"
echo "  Domain: safarzonetravels.com"
echo "  IP: 165.232.178.54"
echo "============================================"
echo

if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root: sudo $0"
    exit 1
fi

echo "[1/7] Updating system..."
apt update && apt upgrade -y

echo
echo "[2/7] Installing essential packages..."
apt install -y python3 python3-pip python3-venv python3-dev
apt install -y nginx
apt install -y postgresql postgresql-contrib libpq-dev
apt install -y build-essential libssl-dev libffi-dev
apt install -y git

echo
echo "[3/7] Creating project directory..."
mkdir -p /var/www/safarzonetravels
chown safar:safar /var/www/safarzonetravels

echo
echo "[4/7] Configuring firewall..."
ufw allow 'Nginx Full'
ufw allow OpenSSH
ufw --force enable

echo
echo "[5/7] Creating Gunicorn service..."
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
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

echo
echo "[6/7] Creating Nginx configuration..."
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

# Enable site
ln -sf /etc/nginx/sites-available/safarzonetravels /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

echo
echo "[7/7] Testing Nginx configuration..."
nginx -t

# Reload systemd
systemctl daemon-reload

echo
echo "============================================"
echo "  Initial Setup Complete!"
echo "============================================"
echo
echo "Next steps:"
echo "1. Switch to safar user: su - safar"
echo "2. Run: cd /var/www/safarzonetravels"
echo "3. Run: bash deploy_with_git.sh"
echo "   (or clone manually: git clone https://github.com/AbdurrabKhan198/travel-company.git .)"
echo

