# PodClipper

A local web app to clip and download audio/video from YouTube — with trim controls, video preview, and proper MP3 tags (title, artist, cover art).

![PodClipper UI](https://i.imgur.com/placeholder.png)

---

## Features

-  Paste a YouTube URL → watch it in-app with the embedded player
-  Drag handles to trim any clip from the video
-  Download as **Song (MP3)** with cover art, title & artist embedded
-  Download as **Video (MP4)** up to 4K
-  Editable song title, artist name, and file name before downloading
-  Keyboard shortcuts: `[` set start · `]` set end · `Space` play/pause · `← →` nudge 1s

---

## Requirements

- Python 3.8+
- [ffmpeg](https://ffmpeg.org/download.html)
- yt-dlp, flask, mutagen (installed automatically — see below)

---

## Setup

### 1. Install Python dependencies
```
pip install -r requirements.txt
```

### 2. Set up ffmpeg

**Option A — Portable (recommended for Windows):**
Download ffmpeg from https://ffmpeg.org/download.html and extract it so the folder structure looks like:
```
PodClipper/
  app.py
  index.html
  ffmpeg/
    bin/
      ffmpeg.exe
      ffprobe.exe
```

**Option B — Install system-wide on Windows:**
```
winget install ffmpeg
```

**Option C — Set an environment variable:**
```
set FFMPEG_BIN=C:\path\to\ffmpeg\bin
```

**Mac/Linux:**
```
brew install ffmpeg       # macOS
sudo apt install ffmpeg   # Ubuntu/Debian
```

### 3. Run

**Windows** — double-click `PodClipper.bat`

**Mac/Linux:**
```
python app.py
```

Then open http://localhost:5000 in your browser.

---

## How to use

1. Paste a YouTube URL and click **Fetch**
2. Watch the video in the built-in player to find your clip
3. Drag the green handles on the trimmer, or press `[` and `]` while playing
4. Choose **Song** or **Video**, edit the title/artist if needed
5. Click **Clip & Download**

---

## License

MIT
