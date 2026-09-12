import os
import json
import requests


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent"
)


def analyze_with_gemini(opportunity, profile):
    if not GEMINI_API_KEY:
        raise RuntimeError(
            "GEMINI_API_KEY is not set"
        )

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

- what the user actually has to do
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
- exact reward or salary
- deadline
- opportunity type
- whether this is a bounty, hackathon, grant, job, or short gig
- how quickly the user could realistically complete it
- whether the opportunity appears legitimate
- whether the opportunity is relevant to the user's interests
- whether the opportunity is realistically accessible to the user

Do NOT assume that an opportunity is suitable simply because it
contains words matching the user's interests.

Be conservative.

If the opportunity clearly requires something the user cannot
meet, mark it as ineligible.

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

"eligible"
= no important eligibility barrier was found.

"uncertain"
= important eligibility information is missing.

"ineligible"
= the user clearly cannot meet an important requirement.

Rules for time_to_money:

"fast"
= could realistically lead to money quickly.

"medium"
= likely takes some time before payment.

"slow"
= long application, competition, grant, long contract,
or otherwise unlikely to produce money quickly.

match_score must be an integer from 0 to 100.

The user's priority is making money soon.

Give extra weight to opportunities that:
- have real monetary rewards
- can be completed quickly
- do not require long hiring processes
- do not require professional licenses
- do not require unnecessary certifications
- are accessible remotely
- match the user's skills

Give lower scores to:
- senior positions
- long hiring processes
- long-term contracts
- unpaid opportunities
- opportunities with unclear compensation
- opportunities with restrictive eligibility

"buggy_take" should be a short, useful explanation of WHY
Buggy thinks the opportunity is or is not worth the user's attention.

Do not exaggerate the opportunity.
"""


    response = requests.post(
        GEMINI_URL,
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
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

    text = (
        data["candidates"][0]
        ["content"]["parts"][0]["text"]
    )

    text = text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    analysis = json.loads(text)

    opportunity["ai_analysis"] = analysis

    return opportunity
