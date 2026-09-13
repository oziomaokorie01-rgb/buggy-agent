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
        try:
            response = requests.get(
                feed_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/rss+xml, application/xml, text/xml, */*"
                },
                timeout=30,
            )
            
            # Skip if status isn't OK or content is empty
            if response.status_code != 200 or not response.content.strip():
                print(f"⚠️ WWR feed returned status {response.status_code} or empty content: {feed_url}")
                continue

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                title = item.findtext("title", "")
                description = item.findtext("description", "")
                link = item.findtext("link", "")

                text = f"{title} {description}".lower()

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
        except ET.ParseError as e:
            print(f"⚠️ XML Parse error for WWR feed {feed_url}: {e}")
        except Exception as e:
            print(f"⚠️ Error fetching WWR feed {feed_url}: {e}")

    return opportunities
