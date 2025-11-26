@echo off
REM ============================================
REM Safar Zone Travels - Production Server Start
REM ============================================
echo.
echo ============================================
echo   Starting Production Server
echo ============================================
echo.

REM Change to project directory
cd /d "%~dp0"

REM Set production environment variables
set DEBUG=False
set SECRET_KEY=django-insecure-t%iz5uu+9-^(kl+^s4=35odc331$*hg5qsa1*plz!h@q4$be(=
set ALLOWED_HOSTS=safarzonetravels.com,www.safarzonetravels.com,165.232.178.54,localhost,127.0.0.1

REM Activate virtual environment if exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Check if Gunicorn is installed
python -c "import gunicorn" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Gunicorn not found. Installing...
    pip install gunicorn
)

echo.
echo Starting Gunicorn server...
echo Domain: safarzonetravels.com
echo IP: 165.232.178.54
echo Port: 8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start Gunicorn
gunicorn Travel_agency.wsgi:application --bind 0.0.0.0:8000 --workers 4 --timeout 120 --access-logfile - --error-logfile -

pause

