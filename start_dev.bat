@echo off
echo ========================================
echo    SBB Weichenheizung - Dev Server
echo ========================================
echo.

cd /d C:\inetpub\whs_app_dev

echo Aktiviere virtuelle Umgebung...
call venv\Scripts\activate.bat

set FLASK_ENV=development
set FLASK_DEBUG=1
set FLASK_PORT=5002

echo Starte Development Server auf Port 5002...
echo URL: https://127.0.0.1:5002  (nur HTTPS - http:// funktioniert nicht)
echo.
echo Druecke Ctrl+C zum Beenden
echo ========================================
echo.

python app.py

pause
