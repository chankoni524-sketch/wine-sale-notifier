import os

import requests
from dotenv import load_dotenv

load_dotenv()

BROADCAST_URL = "https://api.line.me/v2/bot/message/broadcast"
MAX_MESSAGES_PER_REQUEST = 5


def _headers():
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }


def broadcast_texts(texts):
    """テキストのリストを、LINEの1回あたりの送信上限(5件)ごとに分けて送信する。"""
    for i in range(0, len(texts), MAX_MESSAGES_PER_REQUEST):
        chunk = texts[i : i + MAX_MESSAGES_PER_REQUEST]
        body = {"messages": [{"type": "text", "text": t} for t in chunk]}
        response = requests.post(BROADCAST_URL, headers=_headers(), json=body)
        response.raise_for_status()
