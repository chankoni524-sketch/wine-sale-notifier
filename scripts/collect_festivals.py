import json
from pathlib import Path

from festival_search import search_events
from line_notify import broadcast_texts
from storage import filter_new_items

FESTIVAL_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "festivals.json"
FESTIVAL_KEY_FIELDS = ["event_name", "venue", "start_date"]


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


events = search_events()
print(f"検索結果: {len(events)}件")

new_events = filter_new_items(events, FESTIVAL_DATA_FILE, FESTIVAL_KEY_FIELDS)
print(f"うち新着: {len(new_events)}件")
print(json.dumps(new_events, ensure_ascii=False, indent=2))

if new_events:
    broadcast_texts([format_event_message(event) for event in new_events])
    print(f"LINEに{len(new_events)}件送信しました")
else:
    print("新着がないため、LINE送信はスキップしました")
