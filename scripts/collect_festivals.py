import json
from datetime import date, timedelta
from pathlib import Path

from dateutils import is_past, parse_date
from festival_search import search_events
from line_notify import broadcast_texts
from storage import load_seen, make_dedup_key, save_seen

FESTIVAL_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "festivals.json"
FESTIVAL_KEY_FIELDS = ["event_name", "venue", "start_date"]
NOTIFY_WINDOW_DAYS = 31  # 開催開始が通知日から1か月以内のものだけ通知する


def is_within_notify_window(event, today):
    start = parse_date(event.get("start_date"))
    if start is None:
        # 開始日が分からない場合は、通知を止めておく理由もないのでそのまま通知対象にする
        return True
    return today <= start <= today + timedelta(days=NOTIFY_WINDOW_DAYS)


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

    seen = load_seen(FESTIVAL_DATA_FILE)

    newly_stored = 0
    for event in events:
        key = make_dedup_key(event, FESTIVAL_KEY_FIELDS)
        if key not in seen:
            seen[key] = {
                **event,
                "dedup_key": key,
                "first_seen": today.isoformat(),
                "notified": False,
            }
            newly_stored += 1
    print(f"うち新規保存: {newly_stored}件")

    # サイト表示用データは、新規発見分も含めてすぐ保存する(通知の有無とは別)
    save_seen(FESTIVAL_DATA_FILE, seen)

    to_notify = [
        event
        for event in seen.values()
        if not event.get("notified")
        and not is_past(event, today)
        and is_within_notify_window(event, today)
    ]
    print(f"通知対象(開催が1か月以内、未通知のもの): {len(to_notify)}件")
    print(json.dumps(to_notify, ensure_ascii=False, indent=2))

    if to_notify:
        broadcast_texts([format_event_message(event) for event in to_notify])
        for event in to_notify:
            seen[event["dedup_key"]]["notified"] = True
        save_seen(FESTIVAL_DATA_FILE, seen)
        print(f"LINEに{len(to_notify)}件送信しました")
    else:
        print("通知対象がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
