@echo off
title PodClipper
cd /d "%~dp0"

REM Check if server is already running on port 5000
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel%==0 (
    echo PodClipper already running — opening browser...
    start http://localhost:5000
    exit
)

echo Starting PodClipper...
start "" /B python app.py

REM Wait for Flask to boot
timeout /t 2 /nobreak >nul

start http://localhost:5000
exit
