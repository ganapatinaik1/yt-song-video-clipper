# ✂️ yt-clip-downloader

A local web app to clip and download songs and videos from YouTube — with a built-in video player for trimming, proper MP3 tags (title, artist, cover art), and MP4 video up to 4K.

---

## Just double-click `PodClipper.bat` — that's it.

The bat file automatically installs everything it needs (flask, yt-dlp, mutagen) on first run. After that it starts instantly with no reinstalling. Your browser opens to the app automatically.

**The only thing you need installed beforehand is:**
- [Python](https://python.org/downloads) — make sure to check **"Add Python to PATH"** during installation
- [ffmpeg](https://ffmpeg.org/download.html) — install via `winget install ffmpeg` in Command Prompt, or place the `ffmpeg/bin` folder next to `app.py` (see troubleshooting below)

---

## What it does

- Paste any YouTube URL and fetch the video info
- Watch the video inside the app to find exactly where to trim
- Set a start and end point using drag handles or keyboard shortcuts
- Download as **Song (MP3)** — with cover art, title, and artist embedded
- Download as **Video (MP4)** — up to 4K quality
- Edit the song title, artist name, and file name before downloading

---

## Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / Pause |
| `[` | Set trim start at current position |
| `]` | Set trim end at current position |
| `←` | Rewind 1 second |
| `→` | Forward 1 second |

---

## Troubleshooting

If double-clicking the bat doesn't work, follow the steps below.

### Step 1 — Install Python

Download from https://python.org/downloads and run the installer.

**Important:** On the first screen check **"Add Python to PATH"** before clicking Install.

Verify in Command Prompt:
```
python --version
```

### Step 2 — Install ffmpeg

**Option A — winget (easiest):**
```
winget install ffmpeg
```
Close and reopen Command Prompt after.

**Option B — manual:**
1. Download from https://ffmpeg.org/download.html → Windows → gyan.dev → `ffmpeg-release-essentials.zip`
2. Extract it and find the `bin` folder inside
3. Create a folder called `ffmpeg` next to `app.py` and put `bin` inside it:
```
yt-clip-downloader/
  app.py
  index.html
  ffmpeg/
    bin/
      ffmpeg.exe
      ffprobe.exe
```

### Step 3 — Install Python packages manually

Open Command Prompt in the project folder and run:
```
pip install flask yt-dlp mutagen
```

### Step 4 — Run
```
python app.py
```
Then open http://localhost:5000 in your browser.

---

## Common errors

**"Python is not installed"** — Install Python from python.org, check "Add to PATH"

**500 error when fetching a video** — Run `pip install --upgrade yt-dlp` to get the latest version

**ffmpeg not found** — Either `winget install ffmpeg` or place ffmpeg manually next to app.py (see Step 2 above)

**Cover art not showing in Windows Media Player** — Run `pip install mutagen` then download again

**Port 5000 already in use** — Another instance is already running, just go to http://localhost:5000

---

## License

MIT
