#!/bin/bash
# downloadthebeat.sh
# Download songs and videos from YouTube via yt-dlp

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed."
    echo "Install it: sudo apt install python3"
    exit 1
fi

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "Installing ffmpeg..."
    sudo apt update && sudo apt install -y ffmpeg
fi

# Install Python dependencies
echo "Checking dependencies..."
pip3 install flask yt-dlp mutagen -q 2>/dev/null

# Start the server
echo "Starting downloadthebeat..."
python3 app.py &

# Wait for server to start
sleep 3

# Open browser
if command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:5000
elif command -v gnome-open &> /dev/null; then
    gnome-open http://localhost:5000
else
    echo "Open http://localhost:5000 in your browser"
fi

echo "DownloadTheBeat is running at http://localhost:5000"
