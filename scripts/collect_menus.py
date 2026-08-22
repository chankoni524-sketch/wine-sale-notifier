import json
from datetime import date
from pathlib import Path

from dateutils import is_past
from image_utils import image_enrich
from line_notify import broadcast_texts
from menu_search import search_items
from storage import filter_new_items

MENU_DATA_FILE = Path(__file__).resolve().parent.parent / "docs" / "menus.json"
MENU_KEY_FIELDS = ["chain_name", "menu_name", "url"]


def format_menu_message(item):
    lines = [
        "🍽 期間限定メニュー情報",
        f"{item.get('chain_name', '不明')} - {item.get('menu_name', '(メニュー名不明)')}",
    ]
    if item.get("category"):
        lines.append(f"種類: {item['category']}")
    if item.get("price"):
        lines.append(f"価格: {item['price']}")
    period = item.get("start_date", "?")
    if item.get("end_date"):
        period += f" 〜 {item['end_date']}"
    lines.append(f"販売期間: {period}")
    if item.get("url"):
        lines.append(item["url"])
    return "\n".join(lines)


def main():
    items = search_items()
    print(f"検索結果: {len(items)}件")

    today = date.today()
    items = [item for item in items if not is_past(item, today)]
    print(f"うち販売終了していないもの: {len(items)}件")

    new_items = filter_new_items(
        items, MENU_DATA_FILE, MENU_KEY_FIELDS,
        enrich_fn=image_enrich,
    )
    print(f"うち新着: {len(new_items)}件")
    print(json.dumps(new_items, ensure_ascii=False, indent=2))

    if new_items:
        broadcast_texts([format_menu_message(item) for item in new_items])
        print(f"LINEに{len(new_items)}件送信しました")
    else:
        print("新着がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
