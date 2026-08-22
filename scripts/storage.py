import hashlib
import json
from datetime import date
from pathlib import Path

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


def filter_new_items(items, data_file, key_fields):
    """未通知の重複防止キー一覧と比較し、新着分だけを返す。保存ファイルも更新する。"""
    seen = load_seen(data_file)
    new_items = []
    for item in items:
        key = make_dedup_key(item, key_fields)
        if key not in seen:
            item_with_meta = {**item, "dedup_key": key, "first_seen": date.today().isoformat()}
            new_items.append(item_with_meta)
            seen[key] = item_with_meta
    save_seen(data_file, seen)
    return new_items


def filter_new_deals(deals):
    """ワイン用の従来関数(互換のため残す)"""
    return filter_new_items(deals, WINE_DATA_FILE, ["shop", "product_name", "url"])
