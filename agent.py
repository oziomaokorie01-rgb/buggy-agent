import os
import requests

from scanner import search_github_opportunities
from job_scanner import search_job_opportunities

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
    )

    response.raise_for_status()


def format_opportunity(opportunity):
    return (
        f"🐛 NEW OPPORTUNITY\n\n"
        f"🎯 {opportunity['title']}\n\n"
        f"📦 Source: {opportunity.get('source', 'Unknown')}\n"
        f"💰 Reward: {opportunity.get('reward', 'Not specified')}\n\n"
        f"🔗 {opportunity['html_url']}"
    )


def main():
    github_opportunities = search_github_opportunities()
job_opportunities = search_job_opportunities()

opportunities = github_opportunities + job_opportunities

    print(f"🔎 Found {len(opportunities)} potential opportunities")

    if not opportunities:
        print("😴 No opportunities found.")
        return

    for opportunity in opportunities:
        print()
        print(f"🐛 {opportunity['title']}")
        print(f"🔗 {opportunity['html_url']}")

        message = format_opportunity(opportunity)

        send_telegram(message)

        print("📨 Sent to Telegram")


if __name__ == "__main__":
    main()
