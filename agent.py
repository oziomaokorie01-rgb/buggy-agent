import os
import time

import requests
from requests.exceptions import HTTPError

from scanner import search_github_opportunities
from filter import filter_opportunities
from opportunity_agent import evaluate_opportunity
from profile_loader import load_profile
from analyzer import analyze_opportunity
from gemini_analyzer import analyze_with_gemini


# --------------------------------------------------
# CONFIG
# --------------------------------------------------

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

MAX_ALERTS_PER_RUN = 10

PROFILE = load_profile()


# --------------------------------------------------
# GEMINI RETRY
# --------------------------------------------------

def analyze_with_retry(opportunity, profile):
    max_retries = 3

    for attempt in range(max_retries):
        try:
            return analyze_with_gemini(
                opportunity,
                profile
            )

        except HTTPError as error:
            if error.response is not None and error.response.status_code in [429, 503]:
                wait_time = (2 ** attempt) * 2

                print(
                    f"⚠️ Rate limited or server busy. "
                    f"Retrying in {wait_time}s..."
                )

                time.sleep(wait_time)

            else:
                raise

    print(
        f"❌ Failed to analyze: "
        f"{opportunity.get('title', 'Unknown')}"
    )

    return opportunity


# --------------------------------------------------
# TELEGRAM
# --------------------------------------------------

def send_telegram(message):
    if not BOT_TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN is not configured."
        )

    if not CHAT_ID:
        raise RuntimeError(
            "TELEGRAM_CHAT_ID is not configured."
        )

    url = (
        f"https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )

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


# --------------------------------------------------
# TELEGRAM MESSAGE FORMAT
# --------------------------------------------------

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


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print("🐛 Buggy Agent starting...")

    # ----------------------------------------------
    # 1. COLLECT OPPORTUNITIES
    # ----------------------------------------------

    github_opportunities = (
        search_github_opportunities()
    )

    # Remote OK / old job scanner intentionally removed.
    # We will add the approved sources individually.

    all_opportunities = github_opportunities

    print(
        f"🔎 Found "
        f"{len(github_opportunities)} GitHub opportunities"
    )

    # ----------------------------------------------
    # 2. FIRST-PASS FILTER
    # ----------------------------------------------

    worthwhile = filter_opportunities(
        all_opportunities,
        PROFILE
    )

    # ----------------------------------------------
    # 3. RULE-BASED ANALYSIS
    # ----------------------------------------------

    worthwhile = [
        analyze_opportunity(opportunity)
        for opportunity in worthwhile
    ]

    worthwhile = [
        opportunity
        for opportunity in worthwhile
        if opportunity.get("analysis", {}).get(
            "worth_pursuing",
            False
        )
    ]

    print(
        f"🧠 After first-pass filtering: "
        f"{len(worthwhile)} worthwhile opportunities"
    )

    # ----------------------------------------------
    # 4. GEMINI ANALYSIS
    # ----------------------------------------------

    analyzed_opportunities = []

    for opportunity in worthwhile:
        try:
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

            # Prevent excessive Gemini requests.
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

    # ----------------------------------------------
    # 5. LIMIT BEFORE STRANDS
    # ----------------------------------------------

    selected = worthwhile[:MAX_ALERTS_PER_RUN]

    # ----------------------------------------------
    # 6. STRANDS / BUGGY FINAL DECISION
    # ----------------------------------------------

    approved = []

    for opportunity in selected:
        try:
            decision = evaluate_opportunity(
                opportunity
            )

            print()
            print(
                f"🧠 Buggy evaluated: "
                f"{opportunity.get('title', 'Unknown')}"
            )
            print(f"   {decision}")

            if str(decision).upper().startswith("KEEP"):
                approved.append(opportunity)

        except Exception as error:
            print(
                f"⚠️ Buggy evaluation failed for "
                f"{opportunity.get('title', 'Unknown')}: "
                f"{error}"
            )

    selected = approved

    print(
        f"🧠 After Buggy decision: "
        f"{len(selected)} approved opportunities"
    )

    # ----------------------------------------------
    # 7. SEND TELEGRAM ALERTS
    # ----------------------------------------------

    print(
        f"📨 Sending "
        f"{len(selected)} alerts to Telegram"
    )

    for opportunity in selected:
        try:
            message = format_opportunity(
                opportunity
            )

            send_telegram(message)

            print(
                f"✅ Sent: "
                f"{opportunity.get('title', 'Unknown')}"
            )

        except Exception as error:
            print(
                f"❌ Failed to send Telegram alert for "
                f"{opportunity.get('title', 'Unknown')}: "
                f"{error}"
            )

    print("🐛 Buggy Agent finished.")


# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------

if __name__ == "__main__":
    main()
