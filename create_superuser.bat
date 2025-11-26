@echo off
chcp 65001 >nul
title Create Admin User
color 0E
cls

REM ============================================
REM Create Django Superuser
REM ============================================

echo.
echo ============================================
echo   Create Admin User (Superuser)
echo ============================================
echo.

set SERVER_IP=165.232.178.54
set SERVER_USER=safar

echo Connecting to server...
echo.

ssh %SERVER_USER%@%SERVER_IP% "cd /var/www/safarzonetravels && source venv/bin/activate && python manage.py createsuperuser"

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to create superuser!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Superuser Created!
echo ============================================
echo.
echo You can now login at:
echo   http://safarzonetravels.com/admin
echo.
pause

