from datetime import datetime


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def is_past(record, today, end_field="end_date", start_field="start_date"):
    """終了日(なければ開始日)が今日より前なら終了済みとみなす。
    日付の形式が不明な場合は判定できないため、終了済みとはみなさない。"""
    reference_date = parse_date(record.get(end_field)) or parse_date(record.get(start_field))
    if reference_date is None:
        return False
    return reference_date < today
