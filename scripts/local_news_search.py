import json
import os
import re
from datetime import date

import anthropic
from dotenv import load_dotenv

load_dotenv()

TARGET_AREAS = [
    "日暮里駅",
    "西日暮里駅",
    "谷中銀座商店街",
    "町屋駅",
    "上野駅",
    "田端駅",
    "新三河島駅",
    "千駄木駅",
]

PROMPT_TEMPLATE = """\
あなたは特定エリアの地域ニュースを探すリサーチャーです。Web検索を使って、
以下の条件に合う情報を探してください。

本日の日付は __TODAY__ です。

対象エリア(いずれかに該当するものだけを対象とする): __AREAS__

条件:
- 対象エリア内での「新しい商業施設・飲食店の開業」「商業施設・店舗での期間限定イベントの開始」
  「お祭り・地域イベントの開催」に関する情報であること
- 必ず「これから開催・開業される予定」の未来のニュースだけを対象とする。すでに開催・開業した
  ことを報告する記事(過去の出来事のレポート)は対象外
- 開催・開業予定日が本日より前のものは対象外

見つかった情報を、以下のJSON配列の形式だけで出力してください。前置きや説明文は書かず、
JSON配列だけを出力してください(コードブロックの```は付けても付けなくても構いません)。
情報が見つからない場合は空配列 [] を返してください。最大12件程度までに絞ってよい。

[
  {
    "title": "見出し",
    "category": "新規オープン / 期間限定イベント / お祭り のいずれか",
    "area": "該当エリア(駅名など)",
    "location": "具体的な場所・施設名(わかる場合)",
    "event_date": "開始予定日(必ずYYYY-MM-DD形式で)",
    "end_date": "終了予定日(わかる場合、必ずYYYY-MM-DD形式で)",
    "url": "詳細ページのURL",
    "found_summary": "1〜2文の要約"
  }
]
"""


def _build_prompt():
    return (
        PROMPT_TEMPLATE.replace("__AREAS__", "、".join(TARGET_AREAS))
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


def search_news():
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
    news = search_news()
    print(json.dumps(news, ensure_ascii=False, indent=2))
