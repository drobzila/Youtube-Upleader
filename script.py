import requests
import os
import isodate

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

LAST_FILE = "last_video.txt"

# -----------------------------
# 1. Get latest videos
# -----------------------------
def get_videos():
    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "channelId": CHANNEL_ID,
        "order": "date",
        "maxResults": 5,
        "type": "video",
        "key": API_KEY
    }

    res = requests.get(url, params=params, timeout=10).json()

    videos = []

    for item in res.get("items", []):
        videos.append({
            "id": item["id"]["videoId"],
            "title": item["snippet"]["title"]
        })

    return videos


# -----------------------------
# 2. Check if Short
# -----------------------------
def is_short(video_id):
    url = "https://www.googleapis.com/youtube/v3/videos"

    params = {
        "part": "contentDetails",
        "id": video_id,
        "key": API_KEY
    }

    res = requests.get(url, params=params, timeout=10).json()

    items = res.get("items", [])
    if not items:
        return False

    duration = items[0]["contentDetails"]["duration"]
    seconds = isodate.parse_duration(duration).total_seconds()

    return 00 <= seconds <= 60


# -----------------------------
# 3. Check duplicate
# -----------------------------
def already_posted(video_id):
    if not os.path.exists(LAST_FILE):
        return False

    with open(LAST_FILE, "r") as f:
        return video_id.strip() == f.read().strip()


def mark_posted(video_id):
    with open(LAST_FILE, "w") as f:
        f.write(video_id)


# -----------------------------
# 4. Post to Facebook
# -----------------------------
def upload(video_id, title):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    url = f"https://graph.facebook.com/{PAGE_ID}/feed"

    message = f"""🌙 {title}

📺 شاهد الفيديو:
{video_url}

🌿 نسمات القرآن"""

    data = {
        "message": message,
        "access_token": ACCESS_TOKEN
    }

    res = requests.post(url, data=data, timeout=10)
    result = res.json()

    print(result)

    if "error" in result:
        print("❌ فشل النشر في Facebook")
        return False

    print("✔ تم النشر بنجاح")
    return True


# -----------------------------
# 5. Main
# -----------------------------
def main():
    videos = get_videos()

    for v in videos:
        vid = v["id"]

        print("Checking:", vid)

        if already_posted(vid):
            print("⏭ Already posted")
            continue

        if not is_short(vid):
            print("❌ Not Short")
            continue

        success = upload(vid, v["title"])

        if success:
            mark_posted(vid)
            print("✔ Saved as last posted")
            break


if __name__ == "__main__":
    main()
