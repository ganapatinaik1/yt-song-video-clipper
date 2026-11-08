from flask import Flask, request, jsonify, send_file, render_template_string
import subprocess, os, tempfile, glob, json, shutil, platform, sys, urllib.request, urllib.parse, urllib.request, concurrent.futures

app = Flask(__name__)

def _find_ffmpeg():
    """
    Resolve ffmpeg at startup.
    Priority:
      1. FFMPEG_BIN environment variable  (user can point to a custom path)
      2. A 'ffmpeg/bin' folder next to app.py  (portable bundle)
      3. ffmpeg already on the system PATH  (installed via winget / brew / apt)
    """
    env_bin = os.environ.get("FFMPEG_BIN", "").strip()
    if env_bin and os.path.isdir(env_bin):
        return env_bin

    here = os.path.dirname(os.path.abspath(__file__))
    portable = os.path.join(here, "ffmpeg", "bin")
    if os.path.isdir(portable):
        return portable

    exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    found = shutil.which(exe)
    if found:
        return os.path.dirname(found)

    return ""

FFMPEG_BIN = _find_ffmpeg()
FFMPEG_EXE = os.path.join(FFMPEG_BIN, "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg") if FFMPEG_BIN else "ffmpeg"
COOKIES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cookies.txt")
YTDLP_PROXY = os.environ.get("YTDLP_PROXY", "").strip()

INDEX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

@app.route("/")
def index():
    with open(INDEX_PATH, encoding="utf-8") as f:
        return render_template_string(f.read())

@app.route("/cookies-status")
def cookies_status():
    has_cookies = os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0
    return jsonify({"has_cookies": has_cookies})

@app.route("/upload-cookies", methods=["POST"])
def upload_cookies():
    if "cookies_file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    f = request.files["cookies_file"]
    if not f.filename:
        return jsonify({"error": "No file selected"}), 400
    f.save(COOKIES_FILE)
    return jsonify({"success": True, "message": "Cookies saved successfully!"})

@app.route("/search", methods=["POST"])
def search():
    data = request.json or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        is_spotify = "spotify.com" in url or "spotify.link" in url
        is_url = url.startswith("http://") or url.startswith("https://")

        query = ""
        if is_spotify:
            query = ""
            try:
                enc_url = urllib.parse.quote(url, safe="")
                oembed_url = "https://open.spotify.com/oembed?url=" + enc_url
                req = urllib.request.Request(oembed_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp:
                    oembed = json.loads(resp.read().decode("utf-8"))
                title = oembed.get("title", "")
                author = oembed.get("author_name", "")
                query = f"{title} {author}".strip() if title and author else (title or "")
            except Exception as oe:
                return jsonify({"error": "Could not read Spotify link. Try typing the song name instead."}), 400
        elif not is_url:
            query = url
        else:
            return jsonify({"error": "Paste a Spotify link or type a song name to search"}), 400

        if not query:
            return jsonify({"error": "Could not read song name from link"}), 400

        results = []

        def run_yt_dlp(cmd, source):
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if result.returncode == 0:
                    items = []
                    for line in result.stdout.strip().splitlines():
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line)
                        except Exception:
                            continue
                        dur = entry.get("duration") or 0
                        if dur and dur < 30:
                            continue
                        items.append({
                            "source": source,
                            "url": entry.get("webpage_url") or entry.get("url", ""),
                            "title": entry.get("title", "Unknown"),
                            "uploader": entry.get("uploader", ""),
                            "duration": dur,
                            "thumbnail": entry.get("thumbnail", ""),
                            "id": entry.get("id", ""),
                        })
                    return items
            except Exception:
                pass
            return []

        # ── SoundCloud: up to 5 results ──
        sc_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "5",
            f"scsearch5:{query}",
        ]
        if YTDLP_PROXY:
            sc_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            sc_cmd += ["--cookies", COOKIES_FILE]

        # ── JioSaavn: up to 3 results ──
        js_query = urllib.parse.quote(query, safe="")
        js_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "3",
            f"https://www.jiosaavn.com/search/{js_query}",
        ]
        if YTDLP_PROXY:
            js_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            js_cmd += ["--cookies", COOKIES_FILE]

        # ── YouTube Music: up to 5 results (best for Hindi/Bollywood) ──
        yt_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "5",
            f"ytsearch5:{query}",
        ]
        if YTDLP_PROXY:
            yt_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            yt_cmd += ["--cookies", COOKIES_FILE]

        # ── Bandcamp: up to 3 results ──
        bc_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "3",
            f"bandcampsearch:{query}",
        ]
        if YTDLP_PROXY:
            bc_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            bc_cmd += ["--cookies", COOKIES_FILE]

        # ── Audiomack: up to 3 results ──
        am_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "3",
            f"audiomacksearch:{query}",
        ]
        if YTDLP_PROXY:
            am_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            am_cmd += ["--cookies", COOKIES_FILE]

        # ── Audius: up to 3 results ──
        au_cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json", "--no-playlist", "--no-warnings",
            "--flat-playlist", "--max-downloads", "3",
            f"audiussearch:{query}",
        ]
        if YTDLP_PROXY:
            au_cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            au_cmd += ["--cookies", COOKIES_FILE]

        # Run SoundCloud first so results return fast
        sc_results = run_yt_dlp(sc_cmd, "soundcloud")

        # Then run the rest in background while holding SoundCloud results
        other_cmds = [
            (js_cmd, "jiosaavn"),
            (yt_cmd, "youtube"),
            (bc_cmd, "bandcamp"),
            (am_cmd, "audiomack"),
            (au_cmd, "audius"),
        ]
        other_results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(run_yt_dlp, cmd, src) for cmd, src in other_cmds]
            for f in futures:
                try:
                    other_results.extend(f.result(timeout=20))
                except Exception:
                    pass

        results.extend(sc_results)
        results.extend(other_results)

        if not results:
            return jsonify({"error": "No results found on SoundCloud, YouTube, Bandcamp, Audiomack, Audius, or JioSaavn"}), 400

        return jsonify({"results": results})
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Search timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/info", methods=["POST"])
def info():
    data = request.json or {}
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--dump-json",
            "--no-playlist",
            "--no-warnings",
            "--concurrent-fragments", "3",
            "--extractor-args", "youtube:player_client=tv,mweb",
        ]
        if YTDLP_PROXY:
            cmd += ["--proxy", YTDLP_PROXY]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            cmd += ["--cookies", COOKIES_FILE]
        cmd.append(url)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=25)
        if result.returncode != 0:
            err = result.stderr.strip()
            for line in err.splitlines():
                if "ERROR:" in line:
                    err = line.replace("ERROR:", "").strip()
                    break
            return jsonify({"error": err or "Could not fetch video info. Check the URL."}), 400
        meta = json.loads(result.stdout)

        formats = meta.get("formats", [])
        qualities = set()
        for f in formats:
            h = f.get("height")
            if h and f.get("vcodec") != "none":
                qualities.add(h)

        return jsonify({
            "title":     meta.get("title", "Unknown"),
            "duration":  meta.get("duration", 0),
            "thumbnail": meta.get("thumbnail", ""),
            "uploader":  meta.get("uploader", ""),
            "qualities": sorted(qualities, reverse=True)[:6],
            "thumb_url": meta.get("thumbnail", ""),
        })
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Request timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def sanitize_filename(name):
    safe = "".join(c for c in name if c.isalnum() or c in " -_().[]").strip()
    return safe or "podclip"


@app.route("/clip", methods=["POST"])
def clip():
    data       = request.json
    url        = data.get("url", "").strip()
    start_s    = data.get("start_s")
    end_s      = data.get("end_s")
    fmt        = data.get("format", "mp3")
    quality    = data.get("quality", "best")
    song_title = data.get("song_title", "").strip()
    artist     = data.get("artist", "").strip()
    vid_title  = data.get("video_title", "").strip()
    thumb_url  = data.get("thumb_url", "").strip()

    if not url:
        return jsonify({"error": "No URL"}), 400

    def secs_to_ts(s):
        s = float(s)
        h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
        return f"{h}:{m:02d}:{sec:06.3f}"

    tmpdir = tempfile.mkdtemp()
    try:
        out_template = os.path.join(tmpdir, "clip.%(ext)s")
        cmd = [
            sys.executable, "-m", "yt_dlp",
            "--no-playlist",
            "--no-warnings",
            "--concurrent-fragments", "3",
            "--extractor-args", "youtube:player_client=tv,mweb",
            "-o", out_template
        ]
        if YTDLP_PROXY:
            cmd += ["--proxy", YTDLP_PROXY]
        if FFMPEG_BIN:
            cmd += ["--ffmpeg-location", FFMPEG_BIN]
        if os.path.isfile(COOKIES_FILE) and os.path.getsize(COOKIES_FILE) > 0:
            cmd += ["--cookies", COOKIES_FILE]

        need_trim = start_s is not None and start_s > 0
        if need_trim:
            s = secs_to_ts(start_s)
            e = secs_to_ts(end_s) if end_s is not None else None
            if e is not None:
                cmd += ["--download-sections", f"*{s}-{e}", "--force-keyframes-at-cuts"]
            else:
                cmd += ["--download-sections", f"*{s}-*", "--force-keyframes-at-cuts"]

        if fmt == "mp3":
            cmd += ["-x", "--audio-format", "mp3", "--audio-quality", "0"]
        else:
            if quality == "best" or not quality:
                fmt_str = "bestvideo+bestaudio[ext=m4a]/bestvideo+bestaudio/best"
            else:
                fmt_str = (f"bestvideo[height<={quality}]+bestaudio[ext=m4a]/"
                           f"bestvideo[height<={quality}]+bestaudio/"
                           f"best[height<={quality}]/best")
            cmd += ["-f", fmt_str, "--merge-output-format", "mp4"]

        cmd.append(url)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            shutil.rmtree(tmpdir, ignore_errors=True)
            err = result.stderr.strip()
            for line in err.splitlines():
                if "ERROR:" in line:
                    err = line.replace("ERROR:", "").strip()
                    break
            return jsonify({"error": err or "Download failed"}), 500

        files = glob.glob(os.path.join(tmpdir, "*"))
        # Exclude directories like thumb
        files = [f for f in files if os.path.isfile(f)]
        if not files:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return jsonify({"error": "No output file generated"}), 500

        out_file = files[0]
        ext = os.path.splitext(out_file)[1]

        # Embed ID3v2.3 tags via mutagen (WMP-compatible APIC frame)
        if fmt == "mp3":
            try:
                from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError

                tags = ID3(out_file)
            except ID3NoHeaderError:
                tags = ID3()

            try:
                tags.clear()

                if song_title:
                    tags["TIT2"] = TIT2(encoding=3, text=song_title)
                    tags["TALB"] = TALB(encoding=3, text=song_title)
                if artist:
                    tags["TPE1"] = TPE1(encoding=3, text=artist)

                thumb_jpg = None
                if thumb_url:
                    try:
                        thumb_path = os.path.join(tmpdir, "cover.jpg")
                        req = urllib.request.Request(thumb_url, headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
                            "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
                            "Referer": "https://www.youtube.com/",
                        })
                        urllib.request.urlretrieve(thumb_url, thumb_path)
                        if os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                            thumb_jpg = thumb_path
                        else:
                            thumb_jpg = None
                    except Exception:
                        thumb_jpg = None

                if thumb_jpg and os.path.exists(thumb_jpg):
                    with open(thumb_jpg, "rb") as img_f:
                        img_data = img_f.read()
                    tags["APIC"] = APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,
                        desc="Cover",
                        data=img_data
                    )

                tags.save(out_file, v2_version=3)

            except Exception:
                pass

        if fmt == "mp3":
            dl_name = sanitize_filename(song_title or "downloadthebeat") + ".mp3"
        else:
            dl_name = sanitize_filename(vid_title or "downloadthebeat") + ".mp4"

        resp = send_file(
            out_file,
            mimetype="audio/mpeg" if ext == ".mp3" else "video/mp4",
            as_attachment=True,
            download_name=dl_name
        )

        @resp.call_on_close
        def _cleanup():
            shutil.rmtree(tmpdir, ignore_errors=True)

        return resp

    except subprocess.TimeoutExpired:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({"error": "Download timed out"}), 500
    except Exception as e:
        shutil.rmtree(tmpdir, ignore_errors=True)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 5000))
    print(f"PodClipper running at http://{host}:{port}")
    if not FFMPEG_BIN:
        print("WARNING: ffmpeg not found. Place it in a 'ffmpeg/bin' folder next to app.py, or set the FFMPEG_BIN env variable.")
    app.run(host=host, port=port, debug=False)
