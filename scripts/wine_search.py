import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROMPT = """\
あなたはワインの割引セール情報を探すリサーチャーです。Web検索を使って、
現在(できるだけ直近)日本国内で公開されている、以下の条件に合うセール情報を探してください。

条件:
- 商品はワイン(赤・白)のみ(ウイスキーは対象外)
- 1本あたりの通常価格が3000円以上であること
- 割引率が30%以上であること
- 3本以上をまとめたセット商品で、セット価格でしか割引が示されていないもの(1本あたりの価格が
  明確に分からないもの)は対象外。単品、または1〜2本セットで1本あたりの価格が計算できるものだけ対象とする
- 特定の店に限定せず、幅広く探すこと。例:エノテカ、カルディーコーヒーファーム、やまや、リカマン、
  カーヴドリラックス、成城石井、Amazon、楽天市場、Yahoo!ショッピング内の酒販店など、
  日本国内のワイン通販サイトや実店舗のセール情報を広くカバーする
- できるだけ直近(数日以内)に開始・告知されたセール、期間限定セールを優先する
- 通常価格・セール価格が円建ての具体的な数字で確認できないものは対象外とする(「詳細は商品ページ確認」
  としか分からないものは含めない)

見つかった情報を、以下のJSON配列の形式だけで出力してください。前置きや説明文、コードブロックの
装飾(```)は書かないでください。情報が見つからない場合は空配列 [] を返してください。

[
  {
    "product_name": "商品名",
    "category": "wine",
    "shop": "店舗名/サイト名",
    "bottle_count": "1本あたりの価格として扱える本数(1または2)",
    "original_price_per_bottle": "1本あたりの通常価格(数値)",
    "sale_price_per_bottle": "1本あたりのセール価格(数値)",
    "discount_percent": "割引率(数値)",
    "sale_period": "セール期間(わかる場合)",
    "url": "購入/詳細ページのURL",
    "found_summary": "1〜2文の要約"
  }
]
"""


def _extract_json(text):
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def search_deals():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": PROMPT}]
    kwargs = {
        "model": "claude-sonnet-5",
        "max_tokens": 4000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
    }

    response = client.messages.create(messages=messages, **kwargs)
    # 検索を繰り返している間、応答が pause_turn で分割されて返ってくるので、
    # 最終的な回答(end_turn)になるまで続きをリクエストし続ける。
    while response.stop_reason == "pause_turn":
        messages.append({"role": "assistant", "content": response.content})
        response = client.messages.create(messages=messages, **kwargs)

    text_parts = [block.text for block in response.content if block.type == "text"]
    full_text = "\n".join(text_parts)
    try:
        return json.loads(_extract_json(full_text))
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON解析に失敗しました。元の文章:\n{full_text}") from e


if __name__ == "__main__":
    deals = search_deals()
    print(json.dumps(deals, ensure_ascii=False, indent=2))
