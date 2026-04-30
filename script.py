# -*- coding: utf-8 -*-

import os
import time
from typing import Dict, Iterable, List, Optional, Set, Tuple

import isodate
import random
import requests

API_KEY = os.getenv("YOUTUBE_API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
PAGE_ID = os.getenv("FB_PAGE_ID")
ACCESS_TOKEN = os.getenv("FB_ACCESS_TOKEN")

POSTED_FILE = "posted_ids.txt"

YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
FB_FEED_URL = "https://graph.facebook.com/{page_id}/feed"

HTTP_TIMEOUT_S = 15
MAX_SCAN_RESULTS = 200  # scan up to this many recent uploads
YOUTUBE_MAX_RESULTS_PER_PAGE = 50


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

hooks = [
    "✨ هل سمعت هذه الآية من قبل؟",
    "⛔ لا تتجاهل هذا الفيديو...",
    "🌿 دقيقة واحدة قد تغيّر يومك",
    "🤍 رسالة لك اليوم"
]

hook = random.choice(hooks)

def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    params: Optional[dict] = None,
    data: Optional[dict] = None,
    retries: int = 2,
) -> dict:
    last_error: Optional[BaseException] = None

    for attempt in range(retries + 1):
        try:
            res = session.request(
                method,
                url,
                params=params,
                data=data,
                timeout=HTTP_TIMEOUT_S,
            )
            res.raise_for_status()
            return res.json()
        except (requests.RequestException, ValueError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(1.5 * (attempt + 1))
                continue
            raise RuntimeError(f"Request failed: {method} {url}: {e}") from e

    raise RuntimeError(f"Request failed: {method} {url}: {last_error}")


def chunked(items: List[str], size: int) -> Iterable[List[str]]:
    for idx in range(0, len(items), size):
        yield items[idx : idx + size]


def parse_duration_seconds(duration: str) -> float:
    return isodate.parse_duration(duration).total_seconds()


def load_posted() -> Set[str]:
    if not os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "w", encoding="utf-8"):
            pass
        print("⚠️ posted file missing → created new")
        return set()

    with open(POSTED_FILE, "r", encoding="utf-8") as f:
        data = set(line.strip() for line in f if line.strip())

    print(f"📄 Loaded {len(data)} posted videos")
    return data


def mark_posted(video_id: str) -> None:
    with open(POSTED_FILE, "a", encoding="utf-8") as f:
        f.write(video_id + "\n")


def search_recent_videos(
    session: requests.Session, *, page_token: Optional[str] = None
) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    params = {
        "part": "snippet",
        "channelId": CHANNEL_ID,
        "order": "date",
        "maxResults": YOUTUBE_MAX_RESULTS_PER_PAGE,
        "type": "video",
        "key": API_KEY,
    }
    if page_token:
        params["pageToken"] = page_token

    res = request_json(session, "GET", YOUTUBE_SEARCH_URL, params=params)

    videos: List[Tuple[str, str]] = []
    for item in res.get("items", []):
        video_id = (item.get("id") or {}).get("videoId")
        title = (item.get("snippet") or {}).get("title")
        if video_id and title:
            videos.append((video_id, title))

    return videos, res.get("nextPageToken")


def fetch_durations_seconds(
    session: requests.Session, video_ids: List[str]
) -> Dict[str, float]:
    durations: Dict[str, float] = {}

    for batch in chunked(video_ids, 50):
        params = {
            "part": "contentDetails",
            "id": ",".join(batch),
            "key": API_KEY,
        }
        res = request_json(session, "GET", YOUTUBE_VIDEOS_URL, params=params)
        for item in res.get("items", []):
            vid = item.get("id")
            duration = ((item.get("contentDetails") or {}).get("duration")) or ""
            if not vid or not duration:
                continue
            try:
                durations[vid] = parse_duration_seconds(duration)
            except Exception:
                continue

    return durations


def pick_latest_unposted_short(
    session: requests.Session, posted_ids: Set[str]
) -> Optional[Tuple[str, str]]:
    scanned = 0
    page_token: Optional[str] = None

    while scanned < MAX_SCAN_RESULTS:
        videos, page_token = search_recent_videos(session, page_token=page_token)
        if not videos:
            return None

        ids = [vid for (vid, _) in videos]
        durations = fetch_durations_seconds(session, ids)

        for vid, title in videos:
            scanned += 1
            if vid in posted_ids:
                continue

            seconds = durations.get(vid)
            if seconds is None:
                continue

            if 0 <= seconds <= 60:
                return vid, title

            if scanned >= MAX_SCAN_RESULTS:
                break

        if not page_token:
            return None

    return None


def upload_to_facebook(session: requests.Session, video_id: str, title: str) -> bool:
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    url = FB_FEED_URL.format(page_id=PAGE_ID)

    message = f"""{hook}
📺 شاهد الفيديو:
{video_url}

🌙 {title}

🌿 نسمات القرآن"""

    data = {
        "message": message,
        "access_token": ACCESS_TOKEN,
    }

    result = request_json(session, "POST", url, data=data)
    print(result)

    if "error" in result:
        err = result.get("error") or {}
        print(f"❌ فشل النشر في Facebook: {err.get('message', err)}")
        return False

    print("✅ تم النشر بنجاح")
    return True


def main() -> None:
    require_env("YOUTUBE_API_KEY")
    require_env("CHANNEL_ID")
    require_env("FB_PAGE_ID")
    require_env("FB_ACCESS_TOKEN")

    session = requests.Session()

    posted_ids = load_posted()
    print("📌 Already stored IDs:", len(posted_ids))

    picked = pick_latest_unposted_short(session, posted_ids)
    if not picked:
        print("⚠️ No unposted Shorts found (within scan limit)")
        return

    vid, title = picked
    print("🔍 Selected Short:", vid)

    try:
        success = upload_to_facebook(session, vid, title)
    except Exception as e:
        print(f"❌ Upload error: {e}")
        return

    if success:
        mark_posted(vid)
        print("✅ Saved to posted list")


if __name__ == "__main__":
    main()
