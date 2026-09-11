def normalize_opportunity(raw, source):
    return {
        "title": raw.get("title", "").strip(),
        "description": raw.get("description", "").strip(),
        "url": raw.get("url", ""),
        "source": source,
        "reward": raw.get("reward"),
        "deadline": raw.get("deadline"),
        "opportunity_type": raw.get("opportunity_type"),
        "requirements": raw.get("requirements", []),
        "eligibility": raw.get("eligibility"),
        "match_score": 0,
        "match_reasons": []
    }
