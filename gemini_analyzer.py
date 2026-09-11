import os
import json
import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-2.0-flash:generateContent"
)


def analyze_with_gemini(opportunity, profile):
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is not set")

    prompt = f"""
You are Buggy, a personal opportunity scout.

Your job is NOT to blindly recommend opportunities.

You must determine whether this opportunity is realistically
worth the user's attention based on their profile.

USER PROFILE:
{json.dumps(profile, indent=2)}

OPPORTUNITY:
{json.dumps(opportunity, indent=2)}

Analyze the opportunity carefully.

Pay particular attention to:
- required skills
- required experience
- professional licenses
- certifications
- location restrictions
- citizenship restrictions
- education requirements
- application requirements
- CV/resume requirements
- whether payment is actually offered
- deadline
- whether this is a bounty, hackathon, grant, job, or short gig
- how quickly the user could realistically complete it
- whether the opportunity appears legitimate
- whether the opportunity is actually relevant to the user's interests

Do NOT assume that an opportunity is suitable simply because it
contains words matching the user's interests.

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
- "eligible" = no important eligibility barrier found
- "uncertain" = important information is missing
- "ineligible" = the user clearly cannot meet a requirement

Rules for time_to_money:
- "fast" = could realistically lead to money quickly
- "medium" = likely takes some time
- "slow" = long application, competition, grant, long contract, etc.

match_score must be an integer from 0 to 100.

Be conservative.
If a professional license or location restriction clearly excludes
the user, mark the opportunity ineligible.

Do not invent missing information.
"""


    response = requests.post(
        GEMINI_URL,
        params={"key": GEMINI_API_KEY},
        json={
            "contents": [
                {
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        },
        timeout=60,
    )

    response.raise_for_status()

    data = response.json()

    text = data["candidates"][0]["content"]["parts"][0]["text"]

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    analysis = json.loads(text)

    opportunity["ai_analysis"] = analysis

    return opportunity
