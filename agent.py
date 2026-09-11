import os
import requests
from scanner import search_github_opportunities

print("BOT TOKEN EXISTS:", bool(os.getenv("TELEGRAM_BOT_TOKEN")))
print("CHAT ID EXISTS:", bool(os.getenv("TELEGRAM_CHAT_ID")))

opportunities = search_github_opportunities()

print(f"🔎 Found {len(opportunities)} potential opportunities")

for opportunity in opportunities:
    print()
    print(f"🐛 {opportunity['title']}")
    print(f"🔗 {opportunity['html_url']}")
    
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

message = "🐛 Buggy Agent is alive!\n\nGitHub Actions → Telegram is working! ⚡"

url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

response = requests.post(
    url,
    json={
        "chat_id": CHAT_ID,
        "text": message
    }
)

response.raise_for_status()

print("🐛 Buggy Agent successfully sent a Telegram message!")
