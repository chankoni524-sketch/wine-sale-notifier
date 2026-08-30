import json
import os
import re
from datetime import date

import anthropic
from dotenv import load_dotenv

load_dotenv()

TARGET_CHAINS = [
    "ココス",
    "ガスト",
    "デニーズ",
    "オリーブの丘",
    "サイゼリヤ",
    "くら寿司",
    "スシロー",
    "スターバックス",
]

PROMPT_TEMPLATE = """\
あなたは飲食チェーンの新メニュー情報を探すリサーチャーです。Web検索を使って、
以下の8つの店舗チェーンに限定して、季節限定・期間限定・コラボレーションメニューの
最新情報を探してください。これ以外のチェーンは対象外です。

対象チェーン: __CHAINS__

本日の日付は __TODAY__ です。

条件:
- 上記8チェーンのいずれかが公式に発表した、季節限定・期間限定・コラボメニュー
  (新商品・新メニュー)であること
- 通常のレギュラーメニューは対象外
- 販売終了日が本日より前のものは対象外(終了日が不明な場合は対象に含めてよい)
- できるだけ直近に発表された新しいメニューを優先する

見つかった情報を、以下のJSON配列の形式だけで出力してください。前置きや説明文は書かず、
JSON配列だけを出力してください(コードブロックの```は付けても付けなくても構いません)。
情報が見つからない場合は空配列 [] を返してください。見つかった候補が多い場合は、
直近に発表されたものを優先し、最大15件程度までに絞ってよい。

[
  {
    "chain_name": "店舗チェーン名(対象8チェーンのいずれか)",
    "menu_name": "メニュー名",
    "category": "季節限定 / 期間限定 / コラボ のいずれか",
    "price": "価格(わかる場合)",
    "start_date": "販売開始日(わかる場合、必ずYYYY-MM-DD形式で)",
    "end_date": "販売終了日(わかる場合、必ずYYYY-MM-DD形式で)",
    "url": "詳細ページのURL",
    "found_summary": "1〜2文の要約"
  }
]
"""


def _build_prompt():
    return (
        PROMPT_TEMPLATE.replace("__CHAINS__", "、".join(TARGET_CHAINS))
        .replace("__TODAY__", date.today().isoformat())
    )


def _extract_json(text):
    match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r"(\[.*\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return text


def search_items():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": _build_prompt()}]
    kwargs = {
        "model": "claude-sonnet-5",
        "max_tokens": 8000,
        "tools": [{"type": "web_search_20250305", "name": "web_search", "max_uses": 6}],
    }

    response = client.messages.create(messages=messages, **kwargs)
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
    items = search_items()
    print(json.dumps(items, ensure_ascii=False, indent=2))
