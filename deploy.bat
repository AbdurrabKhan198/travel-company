@echo off
title Safar Zone Travels - Deployment
color 0A
REM ============================================
REM Safar Zone Travels - Production Deployment
REM Domain: safarzonetravels.com
REM IP: 165.232.178.54
REM ============================================
cls
echo.
echo ============================================
echo   Safar Zone Travels - Deployment Script
echo   Domain: safarzonetravels.com
echo   IP: 165.232.178.54
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo [1/6] Activating virtual environment (if exists)...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo [OK] Virtual environment activated.
) else (
    echo [INFO] No virtual environment found. Using system Python.
)

echo.
echo [2/6] Installing/Updating dependencies...
pip install -q --upgrade pip
pip install -q -r requirements.txt
if errorlevel 1 (
    echo [WARNING] requirements.txt not found or installation failed.
    echo Continuing with existing packages...
) else (
    echo [OK] Dependencies installed/updated.
)

echo.
echo [3/6] Setting environment variables for production...
set DEBUG=False
set SECRET_KEY=django-insecure-t%iz5uu+9-^(kl+^s4=35odc331$*hg5qsa1*plz!h@q4$be(=
set ALLOWED_HOSTS=safarzonetravels.com,www.safarzonetravels.com,165.232.178.54,localhost,127.0.0.1
echo [OK] Environment variables set.

echo.
echo [4/6] Running database migrations...
python manage.py makemigrations --noinput
python manage.py migrate --noinput
if errorlevel 1 (
    echo [ERROR] Migration failed!
    pause
    exit /b 1
) else (
    echo [OK] Migrations completed.
)

echo.
echo [5/6] Collecting static files...
python manage.py collectstatic --noinput --clear
if errorlevel 1 (
    echo [WARNING] Static files collection failed!
) else (
    echo [OK] Static files collected.
)

echo.
echo [6/6] Deployment preparation complete!
echo.
echo ============================================
echo   SUCCESS! Deployment Ready
echo ============================================
echo.
echo Configuration:
echo   Domain: safarzonetravels.com
echo   IP: 165.232.178.54
echo   DEBUG: False (Production Mode)
echo.
echo Next Steps:
echo   1. Upload files to DigitalOcean server
echo   2. Run this script on the server OR
echo   3. Use production_start.bat to start server
echo.
echo To start production server, run: production_start.bat
echo.
pause

