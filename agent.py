import os
import json
import requests

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def generate_local_fallback(opportunity, profile):
    """Generates a structured analysis locally when API credits are exhausted (402)."""
    title = opportunity.get("title", "")
    desc = opportunity.get("description", "")
    combined_text = f"{title} {desc}".lower()
    
    # Simple heuristic scoring based on user preferences
    match_score = 65
    if any(k in combined_text for k in ["python", "react", "javascript", "ai", "bounty", "remote", "script"]):
        match_score = 85
    elif any(k in combined_text for k in ["senior", "manager", "director", "5+ years"]):
        match_score = 35

    pay_text = opportunity.get("reward") or opportunity.get("salary") or "Not specified in snippet"
    if "[$" in title or "$" in desc:
        pay_text = "Mentioned in listing"

    return {
        "opportunity_type": "bounty/gig" if "bounty" in combined_text or "[$" in title else "remote task",
        "what_you_do": desc[:350] if desc else title,
        "pay": pay_text,
        "deadline": "Not specified",
        "cv_required": False,
        "application_method": "Check opportunity link",
        "experience_required": "Standard remote dev capability",
        "certification_required": False,
        "location_eligibility": "Global / Remote",
        "eligibility_status": "eligible",
        "risk_flags": ["pay_not_specified"] if pay_text == "Not specified in snippet" else [],
        "time_to_money": "fast" if match_score > 70 else "medium",
        "match_score": match_score,
        "worth_pursuing": match_score >= 50,
        "buggy_take": f"Local analysis: Matches your skill keywords with a score of {match_score}%. Worth a quick review."
    }

def analyze_with_gemini(opportunity, profile):
    if not OPENROUTER_API_KEY:
        print("⚠️ OPENROUTER_API_KEY not set. Using local fallback.")
        opportunity["ai_analysis"] = generate_local_fallback(opportunity, profile)
        return opportunity

    prompt = f"""
You are Buggy, a personal opportunity scout.
USER PROFILE:
{json.dumps(profile, indent=2)}
OPPORTUNITY:
{json.dumps(opportunity, indent=2)}
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
        analysis = json.loads(text.strip())
        opportunity["ai_analysis"] = analysis
    except Exception as e:
        # Automatically catch 402, connection errors, or rate limits and switch to local analysis
        print(f"⚠️ API call skipped (Using local fallback engine): {e}")
        opportunity["ai_analysis"] = generate_local_fallback(opportunity, profile)

    return opportunity
