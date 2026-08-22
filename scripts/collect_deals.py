import json

from storage import filter_new_deals
from wine_search import search_deals

deals = search_deals()
print(f"検索結果: {len(deals)}件")

new_deals = filter_new_deals(deals)
print(f"うち新着: {len(new_deals)}件")
print(json.dumps(new_deals, ensure_ascii=False, indent=2))
