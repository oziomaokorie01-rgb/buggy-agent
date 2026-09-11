import requests


def search_github_opportunities():
    url = "https://api.github.com/search/issues"

    params = {
        "q": "bounty is:open",
        "sort": "updated",
        "order": "desc",
        "per_page": 10,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()

    return data.get("items", [])


if __name__ == "__main__":
    opportunities = search_github_opportunities()

    print(f"🔎 Found {len(opportunities)} potential opportunities")

    for opportunity in opportunities:
        print()
        print(f"🐛 {opportunity['title']}")
        print(f"🔗 {opportunity['html_url']}")
