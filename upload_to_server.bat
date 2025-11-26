@echo off
REM ============================================
REM Upload Project Files to DigitalOcean Server
REM Domain: safarzonetravels.com
REM IP: 165.232.178.54
REM ============================================
title Upload to Server
color 0B
cls
echo.
echo ============================================
echo   Upload Project to DigitalOcean Server
echo   Domain: safarzonetravels.com
echo   IP: 165.232.178.54
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0"

echo [INFO] Preparing to upload files...
echo.
echo Source: %CD%
echo Destination: safar@165.232.178.54:/var/www/safarzonetravels/
echo.

REM Check if SCP is available (usually comes with Git for Windows)
where scp >nul 2>&1
if errorlevel 1 (
    echo [ERROR] SCP not found!
    echo.
    echo Please install one of the following:
    echo 1. Git for Windows (includes SCP)
    echo 2. WinSCP (GUI tool)
    echo 3. Use FileZilla (SFTP)
    echo.
    echo Alternative: Use WinSCP or FileZilla to upload files manually
    pause
    exit /b 1
)

echo [INFO] Excluding unnecessary files...
echo.

REM Create .rsync-filter or use scp with exclusions
echo Uploading files (this may take a few minutes)...
echo.

REM Upload files using SCP
scp -r -o StrictHostKeyChecking=no ^
    --exclude="*.pyc" ^
    --exclude="__pycache__" ^
    --exclude=".git" ^
    --exclude="venv" ^
    --exclude="db.sqlite3" ^
    --exclude="*.log" ^
    --exclude=".env" ^
    . safar@165.232.178.54:/var/www/safarzonetravels/

if errorlevel 1 (
    echo.
    echo [ERROR] Upload failed!
    echo.
    echo Please try:
    echo 1. Check SSH connection: ssh safar@165.232.178.54
    echo 2. Verify directory exists on server
    echo 3. Use WinSCP or FileZilla for manual upload
    pause
    exit /b 1
)

echo.
echo ============================================
echo   Upload Complete!
echo ============================================
echo.
echo Next steps on server:
echo 1. SSH: ssh safar@165.232.178.54
echo 2. cd /var/www/safarzonetravels
echo 3. python3 -m venv venv
echo 4. source venv/bin/activate
echo 5. pip install -r requirements.txt
echo 6. python manage.py migrate
echo 7. python manage.py collectstatic
echo 8. Follow SERVER_DEPLOYMENT_STEPS.md
echo.
pause

