import json
from datetime import date, datetime
from pathlib import Path

from festival_search import search_events
from line_notify import broadcast_texts
from storage import filter_new_items

FESTIVAL_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "festivals.json"
FESTIVAL_KEY_FIELDS = ["event_name", "venue", "start_date"]


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def is_past_event(event, today):
    """終了日(なければ開始日)が今日より前なら、終了済みイベントとみなす。
    日付の形式が不明な場合は判定できないため対象外にはしない。"""
    reference_date = _parse_date(event.get("end_date")) or _parse_date(event.get("start_date"))
    if reference_date is None:
        return False
    return reference_date < today


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
    events = [e for e in events if not is_past_event(e, today)]
    print(f"うち開催終了していないもの: {len(events)}件")

    new_events = filter_new_items(events, FESTIVAL_DATA_FILE, FESTIVAL_KEY_FIELDS)
    print(f"うち新着: {len(new_events)}件")
    print(json.dumps(new_events, ensure_ascii=False, indent=2))

    if new_events:
        broadcast_texts([format_event_message(event) for event in new_events])
        print(f"LINEに{len(new_events)}件送信しました")
    else:
        print("新着がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
