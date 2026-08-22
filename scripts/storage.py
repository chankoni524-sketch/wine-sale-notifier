import hashlib
import json
from datetime import date
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "seen_deals.json"


def make_dedup_key(deal):
    raw = f"{deal.get('shop', '')}|{deal.get('product_name', '')}|{deal.get('url', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def load_seen():
    if not DATA_FILE.exists():
        return {}
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def save_seen(seen):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(
        json.dumps(seen, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def filter_new_deals(deals):
    """未通知の重複防止キー一覧と比較し、新着分だけを返す。保存ファイルも更新する。"""
    seen = load_seen()
    new_deals = []
    for deal in deals:
        key = make_dedup_key(deal)
        if key not in seen:
            deal_with_meta = {**deal, "dedup_key": key, "first_seen": date.today().isoformat()}
            new_deals.append(deal_with_meta)
            seen[key] = deal_with_meta
    save_seen(seen)
    return new_deals
