#!/bin/bash
# ============================================
# Safar Zone Travels - Git-based Deployment
# GitHub: https://github.com/AbdurrabKhan198/travel-company.git
# Domain: safarzonetravels.com
# IP: 165.232.178.54
# ============================================

set -e  # Exit on error

echo "============================================"
echo "  Safar Zone Travels - Git Deployment"
echo "  Repository: travel-company"
echo "  Domain: safarzonetravels.com"
echo "============================================"
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
PROJECT_DIR="/var/www/safarzonetravels"
GIT_REPO="https://github.com/AbdurrabKhan198/travel-company.git"
USER="safar"

# Check if running as safar user
if [ "$USER" != "$(whoami)" ]; then
    echo -e "${YELLOW}Switching to safar user...${NC}"
    sudo -u $USER bash -c "$0"
    exit $?
fi

cd $PROJECT_DIR

echo "[1/8] Checking Git installation..."
if ! command -v git &> /dev/null; then
    echo "Installing Git..."
    sudo apt install -y git
fi

echo
echo "[2/8] Checking if repository exists..."
if [ -d ".git" ]; then
    echo -e "${GREEN}Repository found. Pulling latest changes...${NC}"
    git pull origin main || git pull origin master
else
    echo "Cloning repository..."
    if [ "$(ls -A $PROJECT_DIR)" ]; then
        echo -e "${YELLOW}Directory not empty. Backing up and cloning...${NC}"
        cd /tmp
        git clone $GIT_REPO travel-company-temp
        cp -r travel-company-temp/* $PROJECT_DIR/
        cp -r travel-company-temp/.* $PROJECT_DIR/ 2>/dev/null || true
        rm -rf travel-company-temp
        cd $PROJECT_DIR
    else
        git clone $GIT_REPO .
    fi
fi

echo
echo "[3/8] Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate

echo
echo "[4/8] Installing/Updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "[5/8] Setting environment variables..."
export DEBUG=False
# Generate new secret key if needed
if [ -z "$SECRET_KEY" ]; then
    export SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")
    echo -e "${YELLOW}Generated new SECRET_KEY. Save this for production!${NC}"
    echo "SECRET_KEY=$SECRET_KEY" | sudo tee -a /etc/environment
fi
export ALLOWED_HOSTS='safarzonetravels.com,www.safarzonetravels.com,165.232.178.54'

echo
echo "[6/8] Running database migrations..."
python manage.py migrate --noinput

echo
echo "[7/8] Collecting static files..."
python manage.py collectstatic --noinput --clear

echo
echo "[8/8] Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo
echo -e "${GREEN}============================================"
echo "  Deployment Complete!"
echo "============================================${NC}"
echo
echo "Your site should now be live at:"
echo "  http://safarzonetravels.com"
echo "  http://165.232.178.54"
echo
echo "To update in the future, just run this script again!"
echo

