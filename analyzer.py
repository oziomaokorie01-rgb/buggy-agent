def analyze_opportunity(opportunity):
    """
    Performs a first-pass analysis of an opportunity.

    This is the foundation for Buggy's later AI reasoning layer.
    """

    title = opportunity.get("title", "")
    description = opportunity.get("description", "")

    text = f"{title} {description}".lower()

    analysis = {
        "what_you_do": description[:300] if description else title,
        "pay": opportunity.get("reward") or opportunity.get("salary"),
        "deadline": opportunity.get("deadline"),
        "cv_required": False,
        "application_method": "unknown",
        "opportunity_type": opportunity.get(
            "opportunity_type",
            "unknown"
        ),
        "certification_required": False,
        "experience_required": False,
        "eligibility": "unknown",
        "risk_flags": [],
        "worth_pursuing": True
    }

    # CV / resume requirement
    if any(word in text for word in [
        "cv required",
        "resume required",
        "curriculum vitae required"
    ]):
        analysis["cv_required"] = True

    # Professional license / certification
    license_phrases = [
        "license required",
        "licence required",
        "licensed professional",
        "professional license",
        "professional licence",
        "must be licensed",
        "active license"
    ]

    certification_phrases = [
        "certification required",
        "certified required",
        "must be certified",
        "certification is required"
    ]

    if any(phrase in text for phrase in license_phrases):
        analysis["certification_required"] = True
        analysis["risk_flags"].append(
            "professional license required"
        )
        analysis["worth_pursuing"] = False

    if any(phrase in text for phrase in certification_phrases):
        analysis["certification_required"] = True
        analysis["risk_flags"].append(
            "professional certification required"
        )
        analysis["worth_pursuing"] = False

    # Experience requirements
    experience_phrases = [
        "5+ years",
        "5 years experience",
        "5 years of experience",
        "10+ years",
        "10 years experience",
        "senior",
        "principal",
        "lead",
        "director"
    ]

    if any(phrase in text for phrase in experience_phrases):
        analysis["experience_required"] = True
        analysis["risk_flags"].append(
            "advanced experience may be required"
        )

    # Location restrictions
    location_phrases = [
        "us only",
        "usa only",
        "united states only",
        "must be located in the us",
        "must be based in the us",
        "uk only",
        "eu only",
        "europe only",
        "canada only"
    ]

    for phrase in location_phrases:
        if phrase in text:
            analysis["eligibility"] = phrase
            analysis["risk_flags"].append(
                f"location restriction: {phrase}"
            )
            break

    # Application method
    if any(word in text for word in [
        "apply here",
        "application",
        "submit your application",
        "apply now"
    ]):
        analysis["application_method"] = "application"

    elif any(word in text for word in [
        "github issue",
        "open a pull request",
        "pull request",
        "submit a pr"
    ]):
        analysis["application_method"] = "github"

    elif any(word in text for word in [
        "send a dm",
        "dm us",
        "message us"
    ]):
        analysis["application_method"] = "dm"

    opportunity["analysis"] = analysis

    return opportunity
