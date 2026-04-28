import requests
import os
import isodate

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

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

    res = requests.get(url, params=params).json()

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

    res = requests.get(url, params=params).json()

    items = res.get("items", [])
    if not items:
        return False

    duration = items[0]["contentDetails"]["duration"]
    seconds = isodate.parse_duration(duration).total_seconds()

    return seconds <= 60

# -----------------------------
# 3. Post to Facebook (LINK ONLY)
# -----------------------------
def upload(video_id, title):
    video_url = f"https://www.youtube.com/watch?v={video_id}"

    url = f"https://graph.facebook.com/{PAGE_ID}/feed"

    data = {
        "message": f"{title}\n\n📺 {video_url}\n🌿 نسمات القرآن",
        "access_token": ACCESS_TOKEN
    }

    res = requests.post(url, data=data)
    result = res.json()

    print(result)

    # ✔ تحقق حقيقي من النجاح
    if "error" in result:
        print("❌ فشل النشر في Facebook")
        return False

    print("✔ تم النشر بنجاح")
    return True

# -----------------------------
# 4. Main
# -----------------------------
def main():
    videos = get_videos()

    for v in videos:
        vid = v["id"]

        print("Checking:", vid)

        if not is_short(vid):
            print("❌ Not Short")
            continue

        upload(vid, v["title"])

        print("✔ Posted successfully")

        break

if __name__ == "__main__":
    main()
