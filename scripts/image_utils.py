import re

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
}

OG_IMAGE_PATTERNS = [
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']',
]


def fetch_og_image(url, timeout=6):
    """ページのOGP画像(og:image)のURLを取得する。取得できない場合はNoneを返す。"""
    if not url:
        return None
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout)
        response.raise_for_status()
        html = response.text
    except requests.RequestException:
        return None

    for pattern in OG_IMAGE_PATTERNS:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            return match.group(1)
    return None


def image_enrich(item):
    """filter_new_items/sync_and_get_due の enrich_fn 用ヘルパー。
    画像が見つからなかった場合はキーを付けない(後で再取得できるようにする)。"""
    image_url = fetch_og_image(item.get("url"))
    return {"image_url": image_url} if image_url else {}
