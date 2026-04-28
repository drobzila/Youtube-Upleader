import requests
import os
import isodate
import yt_dlp

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAGE_ID = os.getenv("PAGE_ID")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")

# -----------------------------
# 1. Get latest videos
# -----------------------------
def get_latest_videos():
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "channelId": CHANNEL_ID,
        "order": "date",
        "maxResults": 5,
        "type": "video",
        "key": API_KEY
    }

    res = requests.get(url, params=params).json()

    videos = []

    for item in res.get("items", []):
        videos.append({
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"]
        })

    return videos

# -----------------------------
# 2. Check duration (Shorts)
# -----------------------------
def is_short(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "contentDetails",
        "id": video_id,
        "key": API_KEY
    }

    res = requests.get(url, params=params).json()

    items = res.get("items", [])
    if not items:
        return False

    duration = items[0]["contentDetails"]["duration"]
    seconds = isodate.parse_duration(duration).total_seconds()

    return seconds <= 60

# -----------------------------
# 3. Download video
# -----------------------------
def download(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"

    ydl_opts = {
        "outtmpl": "downloads/%(id)s.%(ext)s",
        "format": "mp4"
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

# -----------------------------
# 4. Upload to Facebook Page
# -----------------------------
def upload(video_path, title):
    url = f"https://graph.facebook.com/{PAGE_ID}/videos"

    with open(video_path, "rb") as f:
        files = {"source": f}

        data = {
            "access_token": ACCESS_TOKEN,
            "description": f"{title}\n\n🌿 نسمات القرآن"
        }

        res = requests.post(url, files=files, data=data)

    print(res.json())

# -----------------------------
# 5. Main logic
# -----------------------------
def main():
    videos = get_latest_videos()

    for v in videos:
        vid = v["id"]

        print("Checking:", vid)

        if not is_short(vid):
            print("❌ Not Short")
            continue

        path = download(vid)

        upload(path, v["title"])

        print("✔ Posted successfully")

        break

if __name__ == "__main__":
    main()
