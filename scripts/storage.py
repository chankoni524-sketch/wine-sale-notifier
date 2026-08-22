import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

from dateutils import parse_date

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

WINE_DATA_FILE = DOCS_DIR / "data.json"


def make_dedup_key(item, key_fields):
    raw = "|".join(str(item.get(field, "")) for field in key_fields)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_seen(data_file):
    if not data_file.exists():
        return {}
    return json.loads(data_file.read_text(encoding="utf-8"))


def save_seen(data_file, seen):
    data_file.parent.mkdir(parents=True, exist_ok=True)
    data_file.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def filter_new_items(items, data_file, key_fields, enrich_fn=None):
    """未通知の重複防止キー一覧と比較し、新着分だけを返す。保存ファイルも更新する。
    enrich_fn を渡すと、新着アイテムごとに追加情報(画像URLなど)を付与できる。"""
    seen = load_seen(data_file)
    new_items = []
    for item in items:
        key = make_dedup_key(item, key_fields)
        if key not in seen:
            item_with_meta = {**item, "dedup_key": key, "first_seen": date.today().isoformat()}
            if enrich_fn:
                item_with_meta.update(enrich_fn(item_with_meta) or {})
            new_items.append(item_with_meta)
            seen[key] = item_with_meta
    save_seen(data_file, seen)
    return new_items


def filter_new_deals(deals, enrich_fn=None):
    """ワイン用の従来関数(互換のため残す)"""
    return filter_new_items(deals, WINE_DATA_FILE, ["shop", "product_name", "url"], enrich_fn=enrich_fn)


def sync_and_get_due(items, data_file, key_fields, today, trigger_field, window_days, enrich_fn=None):
    """新着分を保存しつつ(一覧には即掲載)、トリガー日(trigger_field)が今日から
    window_days 日以内に迫っている、まだ未通知のものだけを通知対象として返す。
    トリガー日が読み取れない場合は、判断できないのでそのまま通知対象にする。"""
    seen = load_seen(data_file)
    for item in items:
        key = make_dedup_key(item, key_fields)
        if key not in seen:
            item_with_meta = {**item, "dedup_key": key, "first_seen": today.isoformat(), "notified": False}
            if enrich_fn:
                item_with_meta.update(enrich_fn(item_with_meta) or {})
            seen[key] = item_with_meta
    save_seen(data_file, seen)

    cutoff = today + timedelta(days=window_days)
    due = []
    for item in seen.values():
        if item.get("notified"):
            continue
        trigger = parse_date(item.get(trigger_field))
        if trigger is None or trigger <= cutoff:
            due.append(item)
    return seen, due


def mark_notified(data_file, seen, notified_items):
    for item in notified_items:
        seen[item["dedup_key"]]["notified"] = True
    save_seen(data_file, seen)
