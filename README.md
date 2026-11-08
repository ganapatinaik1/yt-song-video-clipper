downloadthebeat

Download songs and videos from YouTube by pasting a link or searching by song name.

Usage

Windows

Double-click downloadthebeat.bat

The script will:
1. Check if Python is installed
2. Install required Python packages (flask, yt-dlp, mutagen) if missing
3. Check for ffmpeg and install it if possible
4. Start the server at http://localhost:5000
5. Open your browser automatically

Linux

1. Make sure Python 3 is installed:
   python3 --version

2. Install ffmpeg if not present:
   sudo apt update && sudo apt install ffmpeg -y

3. Install Python dependencies:
   pip3 install flask yt-dlp mutagen

4. Start the app:
   python3 app.py

5. Open http://localhost:5000 in your browser

How it works

- Paste a YouTube URL, Spotify link, or type a song keyword into the input box
- If you paste a Spotify link, the app reads the song title and artist, then searches SoundCloud
- Pick a result from the list
- Trim the start and end of the clip using the drag handles
- Click Download to save as MP3 (with title, artist, and cover art) or MP4 (up to 4K)

Troubleshooting

Python not found

Install Python from https://www.python.org/downloads and check "Add Python to PATH" during installation.

ffmpeg not found

Install ffmpeg:
- Windows: winget install ffmpeg
- Linux: sudo apt install ffmpeg

Port 5000 already in use

Another instance is already running. Open http://localhost:5000 in your browser.

No search results

Try a different song name or check your internet connection.
