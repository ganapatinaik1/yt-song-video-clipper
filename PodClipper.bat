@echo off
title PodClipper
cd /d "%~dp0"

REM ── If already running, just open the browser and exit ──────────────────────
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel%==0 (
    echo PodClipper is already running — opening browser...
    start http://localhost:5000
    exit
)

REM ── Check Python is installed ────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not on PATH.
    echo Please download and install Python from https://python.org/downloads
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit
)

REM ── Install / upgrade packages only if missing (fast check, no reinstall) ───
echo Checking dependencies...

python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing flask...
    pip install flask -q
)

python -c "import yt_dlp" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing yt-dlp...
    pip install yt-dlp -q
)

python -c "import mutagen" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing mutagen...
    pip install mutagen -q
)

echo All dependencies ready.

REM ── Start the server ─────────────────────────────────────────────────────────
echo Starting PodClipper...
start "" /B python app.py

REM ── Wait for Flask to boot then open browser ─────────────────────────────────
timeout /t 2 /nobreak >nul
start http://localhost:5000
exit
