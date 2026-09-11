```python
import os
import requests

from scanner import search_github_opportunities
from job_scanner import search_job_opportunities
from filter import filter_opportunities
from profile_loader import load_profile


BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MAX_ALERTS_PER_RUN = 10

PROFILE = load_profile()


def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": CHAT_ID,
            "text": message,
            "disable_web_page_preview": False,
        },
        timeout=30,
    )

    response.raise_for_status()


def format_github_opportunity(opportunity):
    return (
        f"🐛 NEW OPPORTUNITY\n\n"
        f"🎯 {opportunity['title']}\n\n"
        f"📦 Source: GitHub\n"
        f"💰 Reward: {opportunity.get('reward', 'Not specified')}\n"
        f"⭐ Score: {opportunity.get('score', 0)}\n\n"
        f"🔗 {opportunity['html_url']}"
    )


def format_job_opportunity(opportunity):
    return (
        f"🐛 NEW JOB OPPORTUNITY\n\n"
        f"🎯 {opportunity['title']}\n\n"
        f"🏢 Company: {opportunity.get('company', 'Unknown')}\n"
        f"📦 Source: {opportunity.get('source', 'Unknown')}\n"
        f"💰 Salary: {opportunity.get('salary') or 'Not specified'}\n"
        f"⭐ Score: {opportunity.get('score', 0)}\n\n"
        f"🔗 {opportunity['url']}"
    )


def main():
    print("🐛 Buggy Agent starting...")

    github_opportunities = search_github_opportunities()
    job_opportunities = search_job_opportunities()

    all_opportunities = github_opportunities + job_opportunities

    print(
        f"🔎 Found {len(github_opportunities)} GitHub opportunities "
        f"and {len(job_opportunities)} job opportunities"
    )

    worthwhile = filter_opportunities(
        all_opportunities,
        PROFILE
    )

    print(
        f"🧠 After filtering: "
        f"{len(worthwhile)} worthwhile opportunities"
    )

    selected = worthwhile[:MAX_ALERTS_PER_RUN]

    print(
        f"📨 Sending {len(selected)} alerts to Telegram"
    )

    for opportunity in selected:
        if opportunity.get("source") == "GitHub":
            message = format_github_opportunity(opportunity)
        else:
            message = format_job_opportunity(opportunity)

        send_telegram(message)

        print(
            f"✅ Sent: {opportunity['title']}"
        )

    print("🐛 Buggy Agent finished.")


if __name__ == "__main__":
    main()
```
