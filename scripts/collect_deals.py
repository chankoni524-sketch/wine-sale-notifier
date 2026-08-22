import json

from line_notify import broadcast_texts
from storage import filter_new_deals
from wine_search import search_deals


def format_deal_message(deal):
    lines = [
        "🍷 ワイン セール情報",
        deal.get("product_name", "(商品名不明)"),
        f"店舗: {deal.get('shop', '不明')}",
        f"価格: {deal.get('sale_price_per_bottle', '?')}円"
        f"(通常{deal.get('original_price_per_bottle', '?')}円 / "
        f"{deal.get('discount_percent', '?')}%OFF)",
    ]
    if deal.get("sale_period"):
        lines.append(f"期間: {deal['sale_period']}")
    if deal.get("url"):
        lines.append(deal["url"])
    return "\n".join(lines)


def has_price(deal):
    return (
        deal.get("original_price_per_bottle") is not None
        and deal.get("sale_price_per_bottle") is not None
    )


def main():
    deals = search_deals()
    print(f"検索結果: {len(deals)}件")

    filtered = [deal for deal in deals if has_price(deal)]
    print(f"うち価格情報あり: {len(filtered)}件")

    new_deals = filter_new_deals(filtered)
    print(f"うち新着: {len(new_deals)}件")
    print(json.dumps(new_deals, ensure_ascii=False, indent=2))

    if new_deals:
        broadcast_texts([format_deal_message(deal) for deal in new_deals])
        print(f"LINEに{len(new_deals)}件送信しました")
    else:
        print("新着がないため、LINE送信はスキップしました")


if __name__ == "__main__":
    main()
