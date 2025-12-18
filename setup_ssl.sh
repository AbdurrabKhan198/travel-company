#!/bin/bash
# ============================================
# Safar Zone Travels - SSL/HTTPS Setup Script
# Domain: safarzonetravels.com
# IP: 165.232.178.54
# ============================================
# Usage: sudo bash setup_ssl.sh
# ============================================

set -e  # Exit on error

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Safar Zone Travels - SSL/HTTPS Setup${NC}"
echo -e "${BLUE}  Domain: safarzonetravels.com${NC}"
echo -e "${BLUE}============================================${NC}"
echo

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}[ERROR] Please run as root or with sudo${NC}"
    echo "Usage: sudo bash setup_ssl.sh"
    exit 1
fi

# Step 1: Install Certbot
echo -e "${BLUE}[1/4] Installing Certbot...${NC}"
apt update -qq
apt install -y certbot python3-certbot-nginx
echo -e "${GREEN}[OK] Certbot installed.${NC}"

echo
echo -e "${BLUE}[2/4] Checking Nginx configuration...${NC}"
if [ ! -f "/etc/nginx/sites-available/safarzonetravels" ]; then
    echo -e "${RED}[ERROR] Nginx configuration not found!${NC}"
    echo "Please run deployment script first."
    exit 1
fi

# Test Nginx config
nginx -t
echo -e "${GREEN}[OK] Nginx configuration is valid.${NC}"

echo
echo -e "${BLUE}[3/4] Obtaining SSL certificate from Let's Encrypt...${NC}"
echo -e "${YELLOW}[INFO] This will use email: abuhashimazmi@gmail.com${NC}"
echo -e "${YELLOW}[INFO] You will be asked to agree to terms.${NC}"
echo

# Run certbot
certbot --nginx -d safarzonetravels.com -d www.safarzonetravels.com \
    --non-interactive \
    --agree-tos \
    --email abuhashimazmi@gmail.com \
    --redirect

if [ $? -eq 0 ]; then
    echo
    echo -e "${GREEN}[OK] SSL certificate installed successfully!${NC}"
else
    echo
    echo -e "${RED}[ERROR] SSL certificate installation failed!${NC}"
    echo "Please check:"
    echo "1. DNS is pointing to this server (A records: @ and www -> 165.232.178.54)"
    echo "2. Port 80 is open and accessible"
    echo "3. Domain is not already using SSL"
    echo "4. Nginx is running: sudo systemctl status nginx"
    exit 1
fi

echo
echo -e "${BLUE}[4/4] Setting up auto-renewal...${NC}"
# Test auto-renewal
certbot renew --dry-run

if [ $? -eq 0 ]; then
    echo -e "${GREEN}[OK] Auto-renewal configured successfully!${NC}"
else
    echo -e "${YELLOW}[WARNING] Auto-renewal test failed, but certificate is installed.${NC}"
fi

# Restart Nginx to apply changes
systemctl restart nginx
echo -e "${GREEN}[OK] Nginx restarted.${NC}"

echo
echo -e "${GREEN}============================================"
echo -e "  SSL Setup Complete!"
echo -e "============================================${NC}"
echo
echo -e "${GREEN}Your website is now available at:${NC}"
echo -e "  ${BLUE}https://safarzonetravels.com${NC}"
echo -e "  ${BLUE}https://www.safarzonetravels.com${NC}"
echo
echo -e "${YELLOW}HTTP will automatically redirect to HTTPS.${NC}"
echo
echo -e "${BLUE}Certificate will auto-renew every 90 days.${NC}"
echo
echo -e "${GREEN}Check certificate status:${NC}"
echo "  sudo certbot certificates"
echo
echo -e "${GREEN}Test renewal:${NC}"
echo "  sudo certbot renew --dry-run"
echo













