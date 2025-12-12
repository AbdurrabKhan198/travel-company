@echo off
chcp 65001 >nul
title Safar Zone Travels - SSL/HTTPS Setup
color 0B
cls

REM ============================================
REM Safar Zone Travels - SSL/HTTPS Setup
REM Domain: safarzonetravels.com
REM IP: 165.232.178.54
REM ============================================

echo.
echo ============================================
echo   Safar Zone Travels - SSL/HTTPS Setup
echo   Domain: safarzonetravels.com
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0"

echo [STEP 1/3] Checking prerequisites...
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
echo [STEP 2/3] Server Connection Setup
echo.
set /p SERVER_USER="Enter server username (default: root): "
if "%SERVER_USER%"=="" set SERVER_USER=root
set SERVER_IP=165.232.178.54

echo.
echo Connecting to: %SERVER_USER%@%SERVER_IP%
echo.
echo [IMPORTANT] Make sure DNS is configured correctly:
echo   - A Record: @ -^> 165.232.178.54
echo   - A Record: www -^> 165.232.178.54
echo.
pause

REM Run SSL setup on server
echo.
echo [STEP 3/3] Setting up SSL certificate...
echo.

ssh %SERVER_USER%@%SERVER_IP% "bash -s" << 'SSL_SCRIPT'
#!/bin/bash
set -e

echo "============================================"
echo "  SSL/HTTPS Setup for Safar Zone Travels"
echo "============================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Step 1: Install Certbot
echo -e "${BLUE}[1/4] Installing Certbot...${NC}"
apt update -qq
apt install -y certbot python3-certbot-nginx

echo
echo -e "${BLUE}[2/4] Checking Nginx configuration...${NC}"
if [ ! -f "/etc/nginx/sites-available/safarzonetravels" ]; then
    echo -e "${RED}[ERROR] Nginx configuration not found!${NC}"
    echo "Please run deployment script first."
    exit 1
fi

# Test Nginx config
nginx -t

echo
echo -e "${BLUE}[3/4] Obtaining SSL certificate from Let's Encrypt...${NC}"
echo -e "${YELLOW}This will ask for your email address.${NC}"
echo -e "${YELLOW}Press Enter to continue...${NC}"
read

# Run certbot in non-interactive mode with email
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
    echo "1. DNS is pointing to this server"
    echo "2. Port 80 is open and accessible"
    echo "3. Domain is not already using SSL"
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

echo
echo -e "${GREEN}============================================"
echo "  SSL Setup Complete!"
echo "============================================${NC}"
echo
echo -e "${GREEN}Your website is now available at:${NC}"
echo "  https://safarzonetravels.com"
echo "  https://www.safarzonetravels.com"
echo
echo -e "${YELLOW}HTTP will automatically redirect to HTTPS.${NC}"
echo
echo -e "${BLUE}Certificate will auto-renew every 90 days.${NC}"
echo
SSL_SCRIPT

if errorlevel 1 (
    echo.
    echo [ERROR] SSL setup failed!
    echo.
    echo Please check:
    echo 1. DNS is configured correctly (A records pointing to 165.232.178.54)
    echo 2. Port 80 is open and accessible
    echo 3. Domain is not already using SSL
    echo 4. You have root/sudo access
    pause
    exit /b 1
)

echo.
echo ============================================
echo   SUCCESS! SSL/HTTPS Setup Complete!
echo ============================================
echo.
echo Your website is now secure:
echo   https://safarzonetravels.com
echo   https://www.safarzonetravels.com
echo.
echo HTTP will automatically redirect to HTTPS.
echo.
echo Certificate will auto-renew every 90 days.
echo.
pause











