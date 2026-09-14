import os
import time
import requests
from requests.exceptions import HTTPError

from scanner import search_github_opportunities
from wwr_scanner import search_wwr_opportunities
from hn_scanner import search_hn_opportunities
from ai_task_scanner import search_ai_task_opportunities
from filter import filter_opportunities
from opportunity_agent import evaluate_opportunity
from profile_loader import load_profile
from analyzer import analyze_opportunity
from gemini_analyzer import analyze_with_gemini
from history import filter_already_sent, mark_as_sent

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
PROFILE = load_profile()

def analyze_with_retry(opportunity, profile):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return analyze_with_gemini(opportunity, profile)
        except HTTPError as e:
            if e.response.status_code in [429, 503]:
                wait_time = (2 ** attempt) * 2
                print(f"⚠️ Rate limited or server busy. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    print(f"❌ Failed to analyze: {opportunity.get('title')}")
    return opportunity

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

def format_opportunity(opportunity, is_ai_analyzed=True):
    title = opportunity.get("title", "Untitled opportunity")
    url = opportunity.get("html_url") or opportunity.get("url") or ""
    source = opportunity.get("source", "Unknown Source")
    
    if is_ai_analyzed:
        ai = opportunity.get("ai_analysis", {})
        opportunity_type = ai.get("opportunity_type", "Opportunity")
        what_you_do = ai.get("what_you_do", opportunity.get("description", "No description available."))
        pay = ai.get("pay", opportunity.get("reward") or opportunity.get("salary") or "Not specified")
        deadline = ai.get("deadline", "None listed")
        cv_required = "Yes" if ai.get("cv_required") else "No"
        application_method = ai.get("application_method", "Unknown")
        eligibility = ai.get("location_eligibility", "Not specified")
        match_score = ai.get("match_score", 0)
        buggy_take = ai.get("buggy_take", "Worth taking a closer look.")
        time_to_money = ai.get("time_to_money", "unknown")
        
        speed = "⚡ QUICK MONEY" if time_to_money == "fast" else "🕐 MEDIUM TIMELINE" if time_to_money == "medium" else "👀 WORTH A LOOK"

        return (
            f"🐛 BUGGY FOUND SOMETHING (AI Verified)\n\n"
            f"🎯 {title}\n"
            f"📍 Source: {source}\n"
            f"📦 Type: {opportunity_type}\n"
            f"💰 Pay: {pay}\n"
            f"📄 CV: {cv_required}\n"
            f"⏰ Deadline: {deadline}\n\n"
            f"🛠️ What you'll do:\n{what_you_do[:300]}\n\n"
            f"🧠 Buggy's take:\n{buggy_take}\n"
            f"🎯 Match: {match_score}% | {speed}\n\n"
            f"🔗 {url}"
        )
    else:
        # Basic listing for items beyond the top 5 (zero AI token cost)
        desc = opportunity.get("description", "No description available.")
        return (
            f"🐛 BUGGY QUICK LEAD\n\n"
            f"🎯 {title}\n"
            f"📍 Source: {source}\n\n"
            f"📝 Summary:\n{desc[:250]}...\n\n"
            f"🔗 {url}"
        )

def main():
    print("🐛 Buggy Agent starting...")
    
    github_opportunities = search_github_opportunities()
    wwr_opportunities = search_wwr_opportunities()
    hn_opportunities = search_hn_opportunities()
    ai_opportunities = search_ai_task_opportunities()

    all_opportunities = (
        github_opportunities + 
        wwr_opportunities + 
        hn_opportunities + 
        ai_opportunities
    )

    all_opportunities = filter_already_sent(all_opportunities)
    worthwhile = filter_opportunities(all_opportunities, PROFILE)

    print(f"🔎 Found {len(worthwhile)} items passing first-pass filter.")

    # Hard cap workflow output to 10-15 results max
    target_pool = worthwhile[:12]
    
    # Split into Top 5 for deep AI analysis and the rest for basic direct display
    top_5 = target_pool[:5]
    rest_items = target_pool[5:12]

    final_alert_batch = []

    print(f"🧠 Running deep AI analysis on top {len(top_5)} opportunities...")
    for opportunity in top_5:
        try:
            opportunity = analyze_with_retry(opportunity, PROFILE)
            ai_analysis = opportunity.get("ai_analysis", {})
            # Evaluate via Strands or accept if worthwhile
            decision = evaluate_opportunity(opportunity)
            print(f"   - {opportunity['title']} => {decision}")
            
            if decision.upper().startswith("KEEP") or ai_analysis.get("worth_pursuing", True):
                opportunity["_is_ai"] = True
                final_alert_batch.append(opportunity)
            time.sleep(1.0)
        except Exception as error:
            print(f"⚠️ Analysis skipped for {opportunity.get('title', 'Unknown')}: {error}")

    # Add the remaining items as basic listings without hitting LLM APIs
    print(f"📦 Adding {len(rest_items)} direct leads (no AI cost)...")
    for opportunity in rest_items:
        opportunity["_is_ai"] = False
        final_alert_batch.append(opportunity)

    print(f"📨 Sending {len(final_alert_batch)} total alerts to Telegram")

    sent_objects = []
    for opportunity in final_alert_batch:
        is_ai = opportunity.get("_is_ai", False)
        message = format_opportunity(opportunity, is_ai_analyzed=is_ai)
        send_telegram(message)
        sent_objects.append(opportunity)
        print(f"✅ Sent: {opportunity['title']}")

    mark_as_sent(sent_objects)
    print("🐛 Buggy Agent finished.")

if __name__ == "__main__":
    main()
