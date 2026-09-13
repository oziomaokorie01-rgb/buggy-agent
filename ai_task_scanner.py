import requests
import xml.etree.ElementTree as ET

# Feeds or aggregators focusing on AI training, evaluation, contract engineering, and prompt work
AI_FEEDS = [
    "https://weworkremotely.com/categories/remote-back-end-programming-jobs.rss", # often has AI/Python contracts
]

AI_KEYWORDS = [
    "ai trainer",
    "ai training",
    "llm",
    "prompt engineer",
    "data annotation",
    "evaluator",
    "rlhf",
    "nlp",
    "pytorch",
    "openai",
    "claude",
    "ghostwriter",
    "technical writer",
]

def search_ai_task_opportunities():
    opportunities = []
    seen = set()

    for feed_url in AI_FEEDS:
        try:
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

                text_content = f"{title} {description}".lower()

                # Must match AI / task evaluation keywords
                if not any(kw in text_content for kw in AI_KEYWORDS):
                    continue

                if link in seen:
                    continue
                seen.add(link)

                opportunities.append({
                    "id": f"aitask:{link}",
                    "title": title,
                    "description": description,
                    "url": link,
                    "source": "AI & Contract Task Feed",
                    "reward": "",
                    "salary": "",
                })
        except Exception as e:
            print(f"⚠️ Error fetching AI task feed {feed_url}: {e}")

    return opportunities
