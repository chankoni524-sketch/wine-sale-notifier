import json
import os
import re
from datetime import date

import anthropic
from dotenv import load_dotenv

load_dotenv()

PROMPT_TEMPLATE = """\
あなたは東京都内のフードフェス・お祭り情報を探すリサーチャーです。Web検索を使って、
以下の条件に合うイベント情報を探してください。

本日の日付は __TODAY__ です。

条件:
- 開催エリアが東京都23区内であること
- 本日(__TODAY__)以前に終了しているイベントは対象外。まだ開催中、またはこれから開催される
  イベントのみを対象とする(終了日が分からない場合は、開始日が本日以降かどうかで判断する)
- 多数の飲食店・屋台が一か所に集まる大規模フェス・祭りであること。目安として、
  30店舗以上の飲食店・屋台が出店するような規模のイベント(例:パキスタンフェス、台湾フェスティバル、
  肉フェス、世界のごちそう博 など、特定の国・地域や食材をテーマに多数の店が集まるもの)
- 単独のレストラン・カフェが自社内だけで行う期間限定メニューやコラボフェアは対象外
  (店舗数が1〜数店舗程度の企画は含めない)
- 現在開催中のものだけでなく、公式サイトやSNS、ニュースサイトで新しく告知された、
  まだ開催前のイベント情報も積極的に探す(できるだけ早く知りたいため)
- 上野・日暮里・西日暮里・谷中・浅草など台東区・荒川区周辺のエリアで開催されるイベントは
  優先的に探すが、それ以外の23区内のエリアも広く対象とする
- 見つかった候補が多い場合は、上野・台東区周辺に近いものを優先し、最大12件程度までに絞ってよい

見つかった情報を、以下のJSON配列の形式だけで出力してください。前置きや説明文は書かず、
JSON配列だけを出力してください(コードブロックの```は付けても付けなくても構いません)。
情報が見つからない場合は空配列 [] を返してください。

[
  {
    "event_name": "イベント名",
    "theme": "テーマ(国名・地域名・食材名など、わかる場合)",
    "venue": "会場名(例:上野公園 噴水広場)",
    "area": "開催エリア(区名など)",
    "start_date": "開催開始日(わかる場合、YYYY-MM-DD形式に近い形で)",
    "end_date": "開催終了日(わかる場合)",
    "scale_note": "規模が分かる記述(店舗数など。わからない場合は概要から推測できる範囲で)",
    "url": "公式サイトや詳細ページのURL",
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


def _build_prompt():
    return PROMPT_TEMPLATE.replace("__TODAY__", date.today().isoformat())


def search_events():
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
    events = search_events()
    print(json.dumps(events, ensure_ascii=False, indent=2))
