from flask import Flask, request, jsonify, send_file, render_template_string
import subprocess, os, tempfile, glob, json, shutil, platform

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
FFMPEG_EXE = os.path.join(FFMPEG_BIN, "ffmpeg.exe") if (FFMPEG_BIN and platform.system() == "Windows") else "ffmpeg"

HTML = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/info", methods=["POST"])
def info():
    data = request.json
    url = data.get("url", "").strip()
    if not url:
        return jsonify({"error": "No URL provided"}), 400
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return jsonify({"error": "Could not fetch video info. Check the URL."}), 400
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

    if not url:
        return jsonify({"error": "No URL"}), 400

    def secs_to_ts(s):
        s = float(s)
        h = int(s // 3600); m = int((s % 3600) // 60); sec = s % 60
        return f"{h}:{m:02d}:{sec:06.3f}"

    tmpdir = tempfile.mkdtemp()
    try:
        out_template = os.path.join(tmpdir, "clip.%(ext)s")
        cmd = ["yt-dlp", "--no-playlist", "-o", out_template]
        if FFMPEG_BIN:
            cmd += ["--ffmpeg-location", FFMPEG_BIN]

        if start_s is not None or end_s is not None:
            s = secs_to_ts(start_s) if start_s is not None else "0"
            e = secs_to_ts(end_s)   if end_s   is not None else "inf"
            cmd += ["--download-sections", f"*{s}-{e}", "--force-keyframes-at-cuts"]

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
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            return jsonify({"error": result.stderr[-800:] or "Download failed"}), 500

        files = glob.glob(os.path.join(tmpdir, "*"))
        if not files:
            return jsonify({"error": "No output file generated"}), 500

        out_file = files[0]
        ext = os.path.splitext(out_file)[1]

        # Embed ID3v2.3 tags + cover art via mutagen (WMP-compatible APIC frame)
        if fmt == "mp3":
            try:
                from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC, ID3NoHeaderError

                thumb_jpg = None
                try:
                    thumb_dir = os.path.join(tmpdir, "thumb")
                    os.makedirs(thumb_dir, exist_ok=True)
                    thumb_cmd = [
                        "yt-dlp", "--no-playlist",
                        "--write-thumbnail", "--skip-download",
                        "--convert-thumbnails", "jpg",
                        "-o", os.path.join(thumb_dir, "cover.%(ext)s"),
                    ]
                    if FFMPEG_BIN:
                        thumb_cmd += ["--ffmpeg-location", FFMPEG_BIN]
                    thumb_cmd.append(url)
                    subprocess.run(thumb_cmd, capture_output=True, timeout=30)
                    candidates = glob.glob(os.path.join(thumb_dir, "*"))
                    if candidates:
                        raw_thumb = candidates[0]
                        sq_thumb = os.path.join(tmpdir, "cover_sq.jpg")
                        sq_cmd = [
                            FFMPEG_EXE, "-y", "-i", raw_thumb,
                            "-vf", "crop='min(iw,ih)':'min(iw,ih)'",
                            "-q:v", "2", sq_thumb
                        ]
                        r_sq = subprocess.run(sq_cmd, capture_output=True)
                        thumb_jpg = sq_thumb if (r_sq.returncode == 0 and os.path.exists(sq_thumb)) else raw_thumb
                except Exception:
                    thumb_jpg = None

                try:
                    tags = ID3(out_file)
                except ID3NoHeaderError:
                    tags = ID3()

                tags.clear()

                if song_title:
                    tags["TIT2"] = TIT2(encoding=3, text=song_title)
                    tags["TALB"] = TALB(encoding=3, text=song_title)
                if artist:
                    tags["TPE1"] = TPE1(encoding=3, text=artist)

                if thumb_jpg and os.path.exists(thumb_jpg):
                    with open(thumb_jpg, "rb") as img_f:
                        img_data = img_f.read()
                    tags["APIC"] = APIC(
                        encoding=3,
                        mime="image/jpeg",
                        type=3,       # 3 = Cover (front) — required by WMP
                        desc="Cover",
                        data=img_data
                    )

                tags.save(out_file, v2_version=3)  # ID3v2.3 for max WMP compat

            except Exception:
                pass  # Still return audio even if tagging fails

        if fmt == "mp3":
            dl_name = sanitize_filename(song_title or "podclip") + ".mp3"
        else:
            dl_name = sanitize_filename(vid_title or "podclip") + ".mp4"

        return send_file(
            out_file,
            mimetype="audio/mpeg" if ext == ".mp3" else "video/mp4",
            as_attachment=True,
            download_name=dl_name
        )

    except subprocess.TimeoutExpired:
        return jsonify({"error": "Download timed out"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("PodClipper running at http://localhost:5000")
    if not FFMPEG_BIN:
        print("WARNING: ffmpeg not found. Place it in a 'ffmpeg/bin' folder next to app.py, or set the FFMPEG_BIN env variable.")
    app.run(debug=False, port=5000)
