from googleapiclient.discovery import build


def fetch_trending_channels(country_code: str, api_key: str) -> list[dict]:
    youtube = build("youtube", "v3", developerKey=api_key)

    # Step 1: fetch up to 200 trending videos (4 pages × 50)
    channel_data = {}  # channel_id -> {"trending_count": int, "trending_views": int}
    next_page_token = None

    for _ in range(4):
        response = youtube.videos().list(
            part="snippet,statistics",
            chart="mostPopular",
            regionCode=country_code,
            maxResults=50,
            pageToken=next_page_token,
        ).execute()

        for item in response.get("items", []):
            channel_id = item["snippet"]["channelId"]
            views = int(item["statistics"].get("viewCount", 0))
            if channel_id not in channel_data:
                channel_data[channel_id] = {"trending_count": 0, "trending_views": 0}
            channel_data[channel_id]["trending_count"] += 1
            channel_data[channel_id]["trending_views"] += views

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    if not channel_data:
        return []

    # Step 2: fetch channel details in batches of 50
    channel_ids = list(channel_data.keys())
    channels = []

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i:i + 50]
        response = youtube.channels().list(
            part="snippet,statistics",
            id=",".join(batch),
        ).execute()

        for item in response.get("items", []):
            cid = item["id"]
            channels.append({
                "channel_id": cid,
                "name": item["snippet"]["title"],
                "thumbnail": item["snippet"]["thumbnails"].get("default", {}).get("url", ""),
                "subscribers": int(item["statistics"].get("subscriberCount", 0)),
                "trending_count": channel_data[cid]["trending_count"],
                "trending_views": channel_data[cid]["trending_views"],
            })

    return channels
