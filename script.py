import os
import yt_dlp
import requests
import feedparser
import isodate
from dotenv import load_dotenv

load_dotenv()

PAGE_ID = os.getenv("PAGE_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
CHANNEL_URL = os.getenv("CHANNEL_URL")

# -----------------------------
# 1. Get videos list
# -----------------------------
def get_videos():
    feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id=UCHYJMygtSl60pThu6AUgeOw"

    feed = feedparser.parse(feed_url)

    videos = []

    for entry in feed.entries:
        videos.append({
            "id": entry.yt_videoid,
            "title": entry.title
        })

    return videos
        
# -----------------------------
# 2. Filter Shorts (<= 60 sec)
# -----------------------------
def is_short(video_url):
    ydl_opts = {"quiet": True}

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)

        duration = info.get("duration", 0)  # seconds

        return duration <= 60, info

# -----------------------------
# 3. Download video
# -----------------------------
def download_video(url):
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "mp4"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info["id"]

# -----------------------------
# 4. Upload to Facebook
# -----------------------------
def upload(video_path, title):
    url = f"https://graph.facebook.com/{PAGE_ID}/videos"

    files = {"source": open(video_path, "rb")}
    data = {
        "access_token": ACCESS_TOKEN,
        "description": f"{title}\n\n🌿 نسمات القرآن"
    }

    res = requests.post(url, files=files, data=data)
    print(res.json())

def get_videos():
    if not CHANNEL_URL:
        raise Exception("CHANNEL_URL غير موجود في Secrets!")

    ydl_opts = {
        "quiet": True,
        "extract_flat": True
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
        return info.get("entries", [])

# -----------------------------
# 5. Main
# -----------------------------
def main():
    videos = get_videos()

    for v in videos:
        try:
            video_id = v["id"]

            if not video_id:
                continue

            video_url = f"https://www.youtube.com/watch?v={video_id}"

            print("فحص:", video_url)

            short, info = is_short(video_url)

            if not short:
                continue

            video_path, _ = download_video(video_url)

            upload(video_path, info.get("title", "🌿 آية"))

            print("✔ تم النشر")
            break

        except Exception as e:
            print("⚠️ خطأ:", e)
            continue


if __name__ == "__main__":
    main()
