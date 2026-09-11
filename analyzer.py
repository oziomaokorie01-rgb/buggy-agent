def analyze_opportunity(opportunity):
    text = (
        opportunity.get("title", "")
        + " "
        + opportunity.get("description", "")
    ).lower()

    analysis = {
        "what_you_do": "",
        "pay": opportunity.get("reward"),
        "deadline": opportunity.get("deadline"),
        "cv_required": False,
        "application_method": "unknown",
        "opportunity_type": opportunity.get("opportunity_type", "unknown"),
        "certification_required": False,
        "experience_required": False,
        "eligibility": "unknown",
        "risk_flags": [],
        "worth_pursuing": True
    }

    if "cv required" in text or "resume required" in text:
        analysis["cv_required"] = True

    if "license required" in text or "licensed professional" in text:
        analysis["certification_required"] = True
        analysis["risk_flags"].append("professional license required")
        analysis["worth_pursuing"] = False

    if "certification required" in text:
        analysis["certification_required"] = True
        analysis["risk_flags"].append("certification required")
        analysis["worth_pursuing"] = False

    if any(word in text for word in ["senior", "lead", "principal", "director"]):
        analysis["experience_required"] = True
        analysis["risk_flags"].append("advanced experience may be required")

    if "apply" in text:
        analysis["application_method"] = "application"

    if "github issue" in text or "pull request" in text:
        analysis["application_method"] = "github"

    opportunity["analysis"] = analysis

    return opportunity
