@echo off
chcp 65001 >nul
title Update Website
color 0B
cls

REM ============================================
REM Safar Zone Travels - Quick Update Script
REM यह script code update करने के लिए है
REM ============================================

echo.
echo ============================================
echo   Website Update Script
echo   Domain: safarzonetravels.com
echo ============================================
echo.

set /p SERVER_USER="Enter server username (default: safar): "
if "%SERVER_USER%"=="" set SERVER_USER=safar
set SERVER_IP=165.232.178.54

echo.
echo [1/3] Pushing code to GitHub...
echo.
cd /d "%~dp0"

git add .
git commit -m "Update: %date% %time%" 2>nul
git push origin main

if errorlevel 1 (
    echo [WARNING] Git push failed. Continuing anyway...
)

echo.
echo [2/3] Updating server...
echo.

ssh %SERVER_USER%@%SERVER_IP% "bash -s" << 'UPDATE_SCRIPT'
#!/bin/bash
set -e

cd /var/www/safarzonetravels

echo "Pulling latest code from GitHub..."
git pull origin main || git pull origin master

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt -q

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Restarting services..."
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "Update complete!"
UPDATE_SCRIPT

if errorlevel 1 (
    echo.
    echo [ERROR] Update failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Update Complete!
echo ============================================
echo.
echo Your website has been updated.
echo Check: http://safarzonetravels.com
echo.
pause

