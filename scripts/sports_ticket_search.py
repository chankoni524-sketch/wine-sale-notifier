import json
import os
import re
from datetime import date

import anthropic
from dotenv import load_dotenv

load_dotenv()

TARGET_SPORTS = ["サッカー", "バレーボール", "バスケットボール", "バドミントン", "野球"]

PROMPT_TEMPLATE = """\
あなたは日本代表チームの国際大会チケット販売情報を探すリサーチャーです。Web検索を使って、
以下の条件に合う情報を探してください。

本日の日付は __TODAY__ です。

対象スポーツ: __SPORTS__

条件:
- 日本代表チームが出場する国際大会・その予選(ワールドカップ、アジアカップ、オリンピック、
  ネーションズリーグ、国際強化試合など)のうち、日本国内で開催される試合であること
- Jリーグ、Bリーグ、プロ野球公式戦、Vリーグなど国内クラブチームによるリーグ戦は対象外
  (あくまで日本代表としての国際試合のみ)
- 試合そのものの開催告知ではなく、その試合の「観戦チケットの販売開始日」の情報を探す
  (チケット発売日が明記されている情報を優先する)
- 販売開始日がすでに過ぎていても、試合がまだ開催されていなければ対象に含めてよい
- 試合が既に終わっている情報は対象外

見つかった情報を、以下のJSON配列の形式だけで出力してください。前置きや説明文は書かず、
JSON配列だけを出力してください(コードブロックの```は付けても付けなくても構いません)。
情報が見つからない場合は空配列 [] を返してください。最大12件程度までに絞ってよい。

[
  {
    "sport": "対象スポーツのいずれか",
    "competition_name": "大会名(例:FIFAワールドカップ2026アジア最終予選)",
    "match_description": "対戦相手・試合内容の説明",
    "venue": "会場(わかる場合)",
    "match_date": "試合開催日(わかる場合、必ずYYYY-MM-DD形式で)",
    "ticket_sale_date": "チケット販売開始日(必ずYYYY-MM-DD形式で)",
    "url": "詳細ページのURL",
    "found_summary": "1〜2文の要約"
  }
]
"""


def _build_prompt():
    return (
        PROMPT_TEMPLATE.replace("__SPORTS__", "、".join(TARGET_SPORTS))
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


def search_tickets():
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    messages = [{"role": "user", "content": _build_prompt()}]
    kwargs = {
        "model": "claude-sonnet-5",
        "max_tokens": 8000,
        "tools": [{"type": "web_search_20250305", "name": "web_search"}],
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
    items = search_tickets()
    print(json.dumps(items, ensure_ascii=False, indent=2))
