import json
from datetime import date
from pathlib import Path

from dateutils import is_past
from image_utils import image_enrich
from line_notify import broadcast_texts
from local_news_search import search_news
from storage import mark_notified, sync_and_get_due

NEWS_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "local_news.json"
NEWS_KEY_FIELDS = ["title", "url"]
NOTIFY_WINDOW_DAYS = 31  # 開催・開業予定日が通知日から1か月以内のものだけ通知する


def format_news_message(item):
    lines = [
        "📰 地域ニュース",
        item.get("title", "(見出し不明)"),
    ]
    if item.get("category"):
        lines.append(f"種類: {item['category']}")
    lines.append(f"エリア: {item.get('area', '不明')}")
    if item.get("location"):
        lines.append(f"場所: {item['location']}")
    period = item.get("event_date", "?")
    if item.get("end_date"):
        period += f" 〜 {item['end_date']}"
    lines.append(f"予定日: {period}")
    if item.get("url"):
        lines.append(item["url"])
    return "\n".join(lines)


def main():
    items = search_news()
    print(f"検索結果: {len(items)}件")

    today = date.today()
    items = [
        item for item in items
        if not is_past(item, today, end_field="end_date", start_field="event_date")
    ]
    print(f"うち開催予定日が過ぎていないもの: {len(items)}件")

    seen, due = sync_and_get_due(
        items,
        NEWS_DATA_FILE,
        NEWS_KEY_FIELDS,
        today,
        trigger_field="event_date",
        window_days=NOTIFY_WINDOW_DAYS,
        enrich_fn=image_enrich,
    )
    print(f"通知対象(開催・開業が1か月以内、未通知のもの): {len(due)}件")
    print(json.dumps(due, ensure_ascii=False, indent=2))

    if due:
        broadcast_texts([format_news_message(item) for item in due])
        mark_notified(NEWS_DATA_FILE, seen, due)
        print(f"LINEに{len(due)}件送信しました")
    else:
        print("通知対象がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
