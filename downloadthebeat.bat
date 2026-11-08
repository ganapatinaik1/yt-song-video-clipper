@echo off
title downloadthebeat
cd /d "%~dp0"

REM ── If already running, just open the browser and exit ──────────────────────
netstat -ano | findstr ":5000" >nul 2>&1
if %errorlevel%==0 (
    echo downloadthebeat is already running - opening browser...
    start http://localhost:5000
    exit
)

REM ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo ============================================================
    echo  ERROR: Python is not installed.
    echo ============================================================
    echo.
    echo  Please install Python from:
    echo  https://www.python.org/downloads/
    echo.
    echo  IMPORTANT: On the first screen of the installer,
    echo  check the box "Add Python to PATH" before clicking Install.
    echo.
    echo  After installing Python, double-click downloadthebeat.bat again.
    echo ============================================================
    echo.
    pause
    start https://www.python.org/downloads/
    exit
)

REM ── Install packages only if missing ─────────────────────────────────────────
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

REM ── Check ffmpeg ─────────────────────────────────────────────────────────────
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%~dp0ffmpeg\bin\ffmpeg.exe" (
        echo Found portable ffmpeg.
    ) else (
        echo ffmpeg not found - attempting to install via winget...
        winget install ffmpeg --accept-source-agreements --accept-package-agreements -h >nul 2>&1
        if %errorlevel% neq 0 (
            echo.
            echo ============================================================
            echo  WARNING: Could not auto-install ffmpeg.
            echo ============================================================
            echo  Please install it manually:
            echo  1. Open a new Command Prompt and run:
            echo     winget install ffmpeg
            echo  2. Close and reopen this window after.
            echo ============================================================
            echo.
            pause
        ) else (
            echo ffmpeg installed successfully.
        )
    )
)

echo All dependencies ready.
echo.

REM ── Start the server ─────────────────────────────────────────────────────────
echo Starting downloadthebeat...
start "" /B python app.py

REM ── Wait for Flask to boot then open browser ─────────────────────────────────
timeout /t 3 /nobreak >nul
start http://localhost:5000
exit
