import requests


def search_github_opportunities():
    url = "https://api.github.com/search/issues"

    queries = [
        "bounty is:open",
        "reward is:open",
        '"$" bounty is:open',
        "paid is:open",
    ]

    opportunities = []
    seen = set()

    for query in queries:
        params = {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 10,
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        data = response.json()

        for item in data.get("items", []):
            opportunity_id = item["html_url"]

            if opportunity_id in seen:
                continue

            seen.add(opportunity_id)

            opportunities.append({
                "id": opportunity_id,
                "title": item["title"],
                "html_url": item["html_url"],
                "source": "GitHub",
                "reward": extract_reward(item["title"]),
            })

    return opportunities


def extract_reward(title):
    import re

    match = re.search(r"\$\s?[\d,]+(?:\.\d+)?", title)

    if match:
        return match.group(0)

    return "Not specified"
