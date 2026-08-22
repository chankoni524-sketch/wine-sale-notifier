import json
from datetime import date
from pathlib import Path

from dateutils import is_past
from image_utils import image_enrich
from line_notify import broadcast_texts
from sports_ticket_search import search_tickets
from storage import mark_notified, sync_and_get_due

TICKET_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "sports_tickets.json"
TICKET_KEY_FIELDS = ["competition_name", "match_description", "ticket_sale_date"]
NOTIFY_WINDOW_DAYS = 31  # チケット販売開始日が通知日から1か月以内のものだけ通知する


def format_ticket_message(item):
    lines = [
        "🎫 日本代表 チケット販売情報",
        f"{item.get('sport', '')}: {item.get('competition_name', '(大会名不明)')}",
    ]
    if item.get("match_description"):
        lines.append(item["match_description"])
    if item.get("venue"):
        lines.append(f"会場: {item['venue']}")
    if item.get("match_date"):
        lines.append(f"試合日: {item['match_date']}")
    lines.append(f"チケット販売開始日: {item.get('ticket_sale_date', '?')}")
    if item.get("url"):
        lines.append(item["url"])
    return "\n".join(lines)


def main():
    items = search_tickets()
    print(f"検索結果: {len(items)}件")

    today = date.today()
    items = [
        item for item in items
        if not is_past(item, today, end_field="match_date", start_field="match_date")
    ]
    print(f"うち試合が終了していないもの: {len(items)}件")

    seen, due = sync_and_get_due(
        items,
        TICKET_DATA_FILE,
        TICKET_KEY_FIELDS,
        today,
        trigger_field="ticket_sale_date",
        window_days=NOTIFY_WINDOW_DAYS,
        enrich_fn=image_enrich,
    )
    print(f"通知対象(チケット販売開始が1か月以内、未通知のもの): {len(due)}件")
    print(json.dumps(due, ensure_ascii=False, indent=2))

    if due:
        broadcast_texts([format_ticket_message(item) for item in due])
        mark_notified(TICKET_DATA_FILE, seen, due)
        print(f"LINEに{len(due)}件送信しました")
    else:
        print("通知対象がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
