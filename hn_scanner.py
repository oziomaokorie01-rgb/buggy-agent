import requests

ALGOLIA_API_URL = "https://hn.algolia.com/api/v1/search"

KEYWORDS = [
    "remote",
    "contract",
    "freelance",
    "part-time",
    "writer",
    "ai",
    "prompt",
    "engineer",
    "developer",
    "bounty",
    "short-term"
]

def search_hn_opportunities():
    opportunities = []
    seen = set()

    # Search comments specifically inside the "Who's Hiring" threads for remote/freelance keywords
    params = {
        "tags": "comment,author_whoishiring",
        "query": "remote",
        "hitsPerPage": 50
    }

    try:
        response = requests.get(ALGOLIA_API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for hit in data.get("hits", []):
            comment_text = hit.get("comment_text", "")
            if not comment_text:
                continue

            # Basic text check for relevance
            text_lower = comment_text.lower()
            if not any(kw in text_lower for kw in KEYWORDS):
                continue

            # Extract a clean title (first line or first 60 chars)
            clean_text = comment_text.replace("<p>", "\n").replace("</p>", "").replace("</a>", "").replace("<b>", "").replace("</b>", "")
            first_line = clean_text.split("\n")[0].strip()
            title = first_line[:80] if len(first_line) > 5 else "HN Remote / Freelance Gig"

            object_id = hit.get("objectID")
            story_id = hit.get("story_id")
            url = f"https://news.ycombinator.com/item?id={story_id}" if story_id else f"https://news.ycombinator.com/item?id={object_id}"

            if url in seen:
                continue
            seen.add(url)

            opportunities.append({
                "id": f"hn:{object_id}",
                "title": title,
                "description": clean_text,
                "url": url,
                "source": "Hacker News Who's Hiring",
                "reward": "",
                "salary": "",
            })

    except Exception as e:
        print(f"⚠️ Error fetching Hacker News opportunities: {e}")

    return opportunities
