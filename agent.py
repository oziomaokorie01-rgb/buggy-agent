import os
import requests

from scanner import search_github_opportunities
from job_scanner import search_job_opportunities
from filter import filter_opportunities
from profile_loader import load_profile
from analyzer import analyze_opportunity
from gemini_analyzer import analyze_with_gemini
import time
from requests.exceptions import HTTPError

def analyze_with_retry(opportunity, profile):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return analyze_with_gemini(opportunity, profile)
        except HTTPError as e:
            if e.response.status_code in [429, 503]:
                wait_time = (2 ** attempt) * 2  # Exponential backoff: 2s, 4s, 8s
                print(f"⚠️ Rate limited or server busy. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    print(f"❌ Failed to analyze: {opportunity.get('title')}")
    return opportunity
    

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


def format_opportunity(opportunity):
    ai = opportunity.get("ai_analysis", {})

    title = opportunity.get(
        "title",
        "Untitled opportunity"
    )

    opportunity_type = ai.get(
        "opportunity_type",
        opportunity.get(
            "opportunity_type",
            "Opportunity"
        )
    )

    what_you_do = ai.get(
        "what_you_do",
        opportunity.get(
            "description",
            "No description available."
        )
    )

    pay = ai.get(
        "pay",
        opportunity.get("reward")
        or opportunity.get("salary")
        or "Not specified"
    )

    deadline = ai.get(
        "deadline",
        opportunity.get("deadline")
        or "None listed"
    )

    cv_required = (
        "Yes"
        if ai.get("cv_required")
        else "No"
    )

    application_method = ai.get(
        "application_method",
        "Unknown"
    )

    eligibility = ai.get(
        "location_eligibility",
        "Not specified"
    )

    match_score = ai.get(
        "match_score",
        opportunity.get("match_score", 0)
    )

    buggy_take = ai.get(
        "buggy_take",
        "Worth taking a closer look."
    )

    time_to_money = ai.get(
        "time_to_money",
        "unknown"
    )

    if time_to_money == "fast":
        speed = "⚡ QUICK MONEY"
    elif time_to_money == "medium":
        speed = "🕐 MEDIUM TIMELINE"
    elif time_to_money == "slow":
        speed = "🐢 SLOW BURN"
    else:
        speed = "👀 WORTH A LOOK"

    url = (
        opportunity.get("html_url")
        or opportunity.get("url")
        or ""
    )

    return (
        f"🐛 BUGGY FOUND SOMETHING\n\n"
        f"🎯 {title}\n\n"
        f"📦 Type: {opportunity_type}\n"
        f"💰 Pay: {pay}\n"
        f"📄 CV: {cv_required}\n"
        f"📝 Application: {application_method}\n"
        f"⏰ Deadline: {deadline}\n"
        f"🌍 Eligibility: {eligibility}\n\n"
        f"🛠️ What you'll do:\n"
        f"{what_you_do[:400]}\n\n"
        f"🧠 Buggy's take:\n"
        f"{buggy_take}\n\n"
        f"🎯 Match: {match_score}%\n"
        f"{speed}\n\n"
        f"🔗 {url}"
    )


def main():
    print("🐛 Buggy Agent starting...")

    github_opportunities = search_github_opportunities()
    job_opportunities = search_job_opportunities()

    all_opportunities = (
        github_opportunities
        + job_opportunities
    )

    print(
        f"🔎 Found "
        f"{len(github_opportunities)} GitHub opportunities "
        f"and "
        f"{len(job_opportunities)} job opportunities"
    )

    worthwhile = filter_opportunities(
        all_opportunities,
        PROFILE
    )

    worthwhile = [
        analyze_opportunity(opportunity)
        for opportunity in worthwhile
    ]

    worthwhile = [
        opportunity
        for opportunity in worthwhile
        if opportunity["analysis"]["worth_pursuing"]
    ]

    print(
        f"🧠 After first-pass filtering: "
        f"{len(worthwhile)} worthwhile opportunities"
    )

    analyzed_opportunities = []

    for opportunity in worthwhile:
        try:
            # Replaced direct call with retry mechanism
            opportunity = analyze_with_retry(
                opportunity,
                PROFILE
            )

            ai_analysis = opportunity.get(
                "ai_analysis",
                {}
            )

            if ai_analysis.get(
                "worth_pursuing",
                False
            ):
                analyzed_opportunities.append(
                    opportunity
                )

            # Throttle to prevent hitting rate limits (429/503)
            time.sleep(1.5)

        except Exception as error:
            print(
                f"⚠️ Gemini analysis failed for "
                f"{opportunity.get('title', 'Unknown')}: "
                f"{error}"
            )

    worthwhile = analyzed_opportunities

    print(
        f"🤖 After Gemini analysis: "
        f"{len(worthwhile)} worthwhile opportunities"
    )

    selected = worthwhile[:MAX_ALERTS_PER_RUN]

    print(
        f"📨 Sending "
        f"{len(selected)} alerts to Telegram"
    )

    for opportunity in selected:
        message = format_opportunity(
            opportunity
        )

        send_telegram(message)

        print(
            f"✅ Sent: "
            f"{opportunity['title']}"
        )

    print("🐛 Buggy Agent finished.")


if __name__ == "__main__":
    main()
