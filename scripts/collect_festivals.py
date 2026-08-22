import json
from datetime import date
from pathlib import Path

from dateutils import is_past
from festival_search import search_events
from image_utils import image_enrich
from line_notify import broadcast_texts
from storage import mark_notified, sync_and_get_due

FESTIVAL_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "festivals.json"
FESTIVAL_KEY_FIELDS = ["event_name", "venue", "start_date"]
NOTIFY_WINDOW_DAYS = 31  # 開催開始が通知日から1か月以内のものだけ通知する


def format_event_message(event):
    lines = [
        "🎉 フードフェス情報",
        event.get("event_name", "(イベント名不明)"),
    ]
    if event.get("theme"):
        lines.append(f"テーマ: {event['theme']}")
    lines.append(f"会場: {event.get('venue', '不明')}({event.get('area', '不明')})")
    period = event.get("start_date", "?")
    if event.get("end_date"):
        period += f" 〜 {event['end_date']}"
    lines.append(f"開催期間: {period}")
    if event.get("scale_note"):
        lines.append(f"規模: {event['scale_note']}")
    if event.get("url"):
        lines.append(event["url"])
    return "\n".join(lines)


def main():
    events = search_events()
    print(f"検索結果: {len(events)}件")

    today = date.today()
    events = [e for e in events if not is_past(e, today)]
    print(f"うち開催終了していないもの: {len(events)}件")

    seen, due = sync_and_get_due(
        events,
        FESTIVAL_DATA_FILE,
        FESTIVAL_KEY_FIELDS,
        today,
        trigger_field="start_date",
        window_days=NOTIFY_WINDOW_DAYS,
        enrich_fn=image_enrich,
    )
    due = [e for e in due if not is_past(e, today)]
    print(f"通知対象(開催が1か月以内、未通知のもの): {len(due)}件")
    print(json.dumps(due, ensure_ascii=False, indent=2))

    if due:
        broadcast_texts([format_event_message(event) for event in due])
        mark_notified(FESTIVAL_DATA_FILE, seen, due)
        print(f"LINEに{len(due)}件送信しました")
    else:
        print("通知対象がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
