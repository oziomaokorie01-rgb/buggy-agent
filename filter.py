QUICK_WORK_KEYWORDS = [
    "writing",
    "writer",
    "ghostwriter",
    "copywriter",
    "content",
    "blog",
    "social media",
    "ai",
    "ai trainer",
    "ai training",
    "prompt",
    "research",
    "virtual assistant",
]

HIGH_VALUE_KEYWORDS = [
    "paid",
    "bounty",
    "reward",
    "$",
    "usd",
    "freelance",
    "contract",
]

BAD_KEYWORDS = [
    "senior",
    "lead",
    "director",
    "manager",
    "principal",
    "architect",
]


def score_opportunity(opportunity):
    text = (
        str(opportunity.get("title", ""))
        + " "
        + str(opportunity.get("description", ""))
        + " "
        + str(opportunity.get("tags", ""))
    ).lower()

    score = 0

    for keyword in QUICK_WORK_KEYWORDS:
        if keyword in text:
            score += 3

    for keyword in HIGH_VALUE_KEYWORDS:
        if keyword in text:
            score += 2

    for keyword in BAD_KEYWORDS:
        if keyword in text:
            score -= 4

    if opportunity.get("reward"):
        score += 3

    if opportunity.get("salary"):
        score += 3

    return score


def filter_opportunities(opportunities, minimum_score=4):
    scored = []

    for opportunity in opportunities:
        score = score_opportunity(opportunity)

        if score >= minimum_score:
            opportunity["score"] = score
            scored.append(opportunity)

    scored.sort(
        key=lambda opportunity: opportunity["score"],
        reverse=True,
    )

    return scored
