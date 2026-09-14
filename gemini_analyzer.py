import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def generate_local_fallback(opportunity, profile):
    """Generates a structured analysis locally when OpenRouter API is unavailable or out of credits (402)."""
    title = opportunity.get("title", "")
    desc = opportunity.get("description", "")
    combined_text = f"{title} {desc}".lower()
    
    # Smart heuristic scoring based on developer profile keywords
    match_score = 65
    dev_keywords = ["python", "react", "javascript", "ai", "bounty", "remote", "script", "fix", "issue", "web"]
    if any(k in combined_text for k in dev_keywords):
        match_score = 80
    elif any(k in combined_text for k in ["senior", "director", "5+ years", "manager"]):
        match_score = 35

    pay_text = opportunity.get("reward") or opportunity.get("salary") or "Not specified in snippet"
    if "$" in combined_text or "bounty" in combined_text:
        pay_text = "Mentioned in listing"

    return {
        "opportunity_type": "bounty/gig" if ("bounty" in combined_text or "$" in combined_text) else "remote task",
        "what_you_do": desc[:350] if desc else title,
        "pay": pay_text,
        "deadline": "Not specified",
        "cv_required": False,
        "application_method": "Check link",
        "experience_required": "Standard remote dev capability",
        "certification_required": False,
        "location_eligibility": "Global / Remote",
        "eligibility_status": "eligible",
        "risk_flags": [],
        "time_to_money": "fast" if match_score >= 70 else "medium",
        "match_score": match_score,
        "worth_pursuing": match_score >= 40,
        "buggy_take": f"Local Fallback Analysis: Matches your developer skills with a match score of {match_score}%."
    }

def analyze_with_gemini(opportunity, profile):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY is not set. Using local fallback.")
        opportunity["ai_analysis"] = generate_local_fallback(opportunity, profile)
        return opportunity

    prompt = f"""
You are Buggy, a personal opportunity scout.

Your job is to determine whether this opportunity is realistically
worth the user's attention based on their profile.

USER PROFILE:
{json.dumps(profile, indent=2)}

OPPORTUNITY:
{json.dumps(opportunity, indent=2)}

Analyze the opportunity carefully.

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
"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/buggy-agent",
                "X-Title": "Buggy Agent"
            },
            json={
                "model": "google/gemma-2-9b-it:free",
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "max_tokens": 800
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        text = data["choices"][0]["message"]["content"].strip()

        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]

        opportunity["ai_analysis"] = json.loads(text.strip())
    except Exception as e:
        print(f"⚠️ OpenRouter API hit an issue ({e}). Switching seamlessly to local fallback analysis.")
        opportunity["ai_analysis"] = generate_local_fallback(opportunity, profile)

    return opportunity
