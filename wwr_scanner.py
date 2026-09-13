import requests
import xml.etree.ElementTree as ET


WWR_FEEDS = [
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-sales-and-marketing-jobs.rss",
    "https://weworkremotely.com/categories/remote-other-jobs.rss",
]

KEYWORDS = [
    "writing",
    "writer",
    "ghostwriter",
    "copywriter",
    "content",
    "blog",
    "social media",
    "ai",
    "prompt",
    "research",
    "design",
    "ui",
    "ux",
    "freelance",
    "contract",
    "project",
    "bounty",
]


def search_wwr_opportunities():
    opportunities = []
    seen = set()

    for feed_url in WWR_FEEDS:
        response = requests.get(
            feed_url,
            headers={"User-Agent": "Buggy-Agent/1.0"},
            timeout=30,
        )
        response.raise_for_status()

        root = ET.fromstring(response.content)

        for item in root.findall(".//item"):
            title = item.findtext("title", "")
            description = item.findtext("description", "")
            link = item.findtext("link", "")

            text = (
                f"{title} {description}"
            ).lower()

            if not any(keyword in text for keyword in KEYWORDS):
                continue

            if link in seen:
                continue

            seen.add(link)

            opportunities.append({
                "id": f"wwr:{link}",
                "title": title,
                "description": description,
                "url": link,
                "source": "We Work Remotely",
                "reward": "",
                "salary": "",
            })

    return opportunities
