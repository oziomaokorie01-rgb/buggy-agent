import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def analyze_with_gemini(opportunity, profile):
    if not OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    prompt = f"""
You are Buggy, a personal opportunity scout.

Your job is to determine whether this opportunity is realistically
worth the user's attention based on their profile.

USER PROFILE:
{json.dumps(profile, indent=2)}

OPPORTUNITY:
{json.dumps(opportunity, indent=2)}

Analyze the opportunity carefully.

Pay particular attention to:

- what the user actually has to do
- required skills
- required experience
- whether payment is actually offered
- exact reward or salary
- deadline
- opportunity type (bounty, hackathon, grant, job, or short gig)
- how quickly the user could realistically complete it
- whether the opportunity is relevant and accessible

Be practical, not overly restrictive.

If an opportunity is a reasonable fit for a remote developer, quick gig, or bounty, mark it as worth pursuing (worth_pursuing: true) if the match score is 40 or higher, even if some minor details are unspecified.

Do not invent missing information.

Return ONLY valid JSON in exactly this structure:

{{
  "opportunity_type": "",
  "what_you_do": "",
  "pay": "",
  "deadline": "",
  "cv_required": false,
  "application_method": "",
  "experience_required": "",
  "certification_required": false,
  "location_eligibility": "",
  "eligibility_status": "eligible",
  "risk_flags": [],
  "time_to_money": "fast",
  "match_score": 0,
  "worth_pursuing": true,
  "buggy_take": ""
}}

Rules for eligibility_status:
"eligible" = no important eligibility barrier was found.
"uncertain" = important eligibility information is missing.
"ineligible" = the user clearly cannot meet an important requirement.

Rules for time_to_money:
"fast" = could realistically lead to money quickly.
"medium" = likely takes some time before payment.
"slow" = long application, competition, grant, or long contract.

match_score must be an integer from 0 to 100.
The user's priority is making money soon.

"buggy_take" should be a short, useful explanation of WHY
Buggy thinks the opportunity is or is not worth the user's attention.
"""

    response = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/buggy-agent",
            "X-Title": "Buggy Agent"
        },
        json={
            "model": "openrouter/auto",
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        },
        timeout=60,
    )

    if not response.ok:
        print("❌ OpenRouter error:")
        print(response.text)
        response.raise_for_status()
    data = response.json()
    text = data["choices"][0]["message"]["content"]

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    analysis = json.loads(text)
    print("🧠 AI ANALYSIS:")
    print(json.dumps(analysis, indent=2))

    opportunity["ai_analysis"] = analysis

    return opportunity
