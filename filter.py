import re

# Keywords that indicate actual monetization, task-based work, or quick payouts
PRIORITY_KEYWORDS = [
    "bounty",
    "reward",
    "paid",
    "$",
    "usdc",
    "usdt",
    "grant",
    "hackathon",
    "contract",
    "freelance",
    "gig",
    "part-time",
    "writing",
    "writer",
    "ghostwriter",
    "copywriter",
    "content",
    "prompt",
    "ai evaluation",
    "research",
    "design",
    "ui/ux",
]

# Keywords that instantly disqualify an item (noise, maintenance PRs, senior requirements)
EXCLUDE_KEYWORDS = [
    "update dependency",
    "deps",
    "chore(deps)",
    "security advisory",
    "lockfile",
    "senior engineering manager",
    "director of",
    "vp of",
    "unpaid intern",
    "volunteer",
]

def filter_opportunities(opportunities, profile):
    filtered = []

    for opp in opportunities:
        title = opp.get("title", "").lower()
        description = opp.get("description", "").lower()
        full_text = f"{title} {description}"

        # 1. Check exclusions first
        if any(exc in full_text for exc in EXCLUDE_KEYWORDS):
            continue

        # 2. For GitHub issues, heavily favor those containing money markers or explicit bounty labels
        source = opp.get("source", "")
        if source == "GitHub":
            # Check if it has monetary markers or is explicitly a task/bounty
            has_money = any(token in full_text for token in ["$", "bounty", "reward", "paid", "usdc"])
            has_task_label = any(lbl in str(opp.get("labels", [])).lower() for lbl in ["bounty", "good first issue", "help wanted", "paid"])
            
            if not (has_money or has_task_label):
                # If it's a generic GitHub issue without financial/task indicators, skip it
                continue

        # 3. For WWR / HN / general sources, check against priority keywords
        if source != "GitHub":
            if not any(kw in full_text for kw in PRIORITY_KEYWORDS):
                continue

        filtered.append(opp)

    return filtered
