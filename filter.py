def filter_opportunities(opportunities, profile):
    filtered = []

    interests = set(profile.get("interests", []))
    opportunity_types = set(profile.get("opportunity_types", []))
    avoid = set(profile.get("avoid", []))

    for opportunity in opportunities:
        text = " ".join(
            str(opportunity.get(key, ""))
            for key in ["title", "description", "url"]
        ).lower()

        score = 0
        reasons = []

        # Interest matching
        interest_keywords = {
            "development": ["developer", "software", "code", "github", "programming"],
            "ai": ["ai", "artificial intelligence", "machine learning", "llm", "prompt"],
            "security": ["security", "bug bounty", "vulnerability", "pentest"],
            "writing": ["writer", "writing", "content", "copywriter", "documentation"],
            "design": ["design", "ui", "ux", "figma"],
            "research": ["research", "analysis", "analyst"]
        }

        for interest in interests:
            for keyword in interest_keywords.get(interest, []):
                if keyword in text:
                    score += 2
                    reasons.append(f"matches {interest}")
                    break

        # Opportunity type matching
        type_keywords = {
            "bounty": ["bounty", "reward", "bug bounty"],
            "quick_gig": ["freelance", "short-term", "one-off", "fixed price"],
            "hackathon": ["hackathon", "competition", "challenge"],
            "grant": ["grant", "funding", "fellowship"],
            "short_contract": ["contract", "temporary", "short-term"],
            "remote_job": ["remote", "full-time", "part-time"]
        }

        for opportunity_type in opportunity_types:
            for keyword in type_keywords.get(opportunity_type, []):
                if keyword in text:
                    score += 2
                    reasons.append(f"matches {opportunity_type}")
                    break

        # Things the user explicitly wants to avoid
        avoid_keywords = {
            "senior_role": ["senior", "lead", "principal", "director", "manager"],
            "certification_required": [
                "license required",
                "certification required",
                "licensed",
                "professional certification"
            ],
            "long_contract": [
                "12 month",
                "12-month",
                "long term",
                "long-term contract"
            ],
            "unpaid": [
                "unpaid",
                "volunteer",
                "no compensation"
            ]
        }

        rejected = False

        for avoidance in avoid:
            for keyword in avoid_keywords.get(avoidance, []):
                if keyword in text:
                    rejected = True
                    break

            if rejected:
                break

        if rejected:
            continue

        if score >= 2:
            opportunity["match_score"] = min(score * 10, 100)
            opportunity["match_reasons"] = list(dict.fromkeys(reasons))
            filtered.append(opportunity)

    return filtered
