import os

import requests
from dotenv import load_dotenv

load_dotenv()

ACCESS_TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

url = "https://api.line.me/v2/bot/message/broadcast"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ACCESS_TOKEN}",
}
body = {
    "messages": [
        {"type": "text", "text": "テスト通知:このメッセージが届けば、プログラムからLINEへの送信は成功です。"}
    ]
}

response = requests.post(url, headers=headers, json=body)
print(response.status_code, response.text)
