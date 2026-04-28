import requests
import os
import isodate

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

POSTED_FILE = "posted_ids.txt"

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

def load_posted():
    if not os.path.exists(POSTED_FILE):
        print("⚠️ posted file not found → creating new")
        return set()

    with open(POSTED_FILE, "r", encoding="utf-8") as f:
        data = set(line.strip() for line in f if line.strip())

    print(f"📄 Loaded {len(data)} posted videos")
    return data

def mark_posted(video_id):
    with open(POSTED_FILE, "a") as f:
        f.write(video_id + "\n")

# 3. Check duplicate
# -----------------------------
def already_posted(video_id):
    if not os.path.exists(POSTED_FILE):
        return False

    with open(POSTED_FILE, "r") as f:
        return video_id.strip() == f.read().strip()


def mark_posted(video_id):
    with open(POSTED_FILE, "w") as f:
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

    if not videos:
        print("⚠️ No videos found")
        return

    posted_ids = load_posted()
    posted_any = False   # 🔥 هذا هو الحل

    for v in videos:
        vid = v["id"]
        title = v["title"]

        print("🔍 Checking:", vid)

        if vid in posted_ids:
            print("⏭ Already posted")
            continue

        if not is_short(vid):
            print("❌ Not Short")
            continue

        try:
            success = upload(vid, title)
        except Exception as e:
            print(f"❌ Upload error: {e}")
            continue

        if success:
            mark_posted(vid)
            posted_any = True
            print("✔ Saved to posted list")
            break

    if not posted_any:
        print("ℹ️ No new videos were posted today")

if __name__ == "__main__":
    main()
