import requests


REMOTE_OK_API = "https://remoteok.com/api"


KEYWORDS = [
    "writing",
    "writer",
    "ghostwriter",
    "copywriter",
    "content",
    "content writer",
    "social media",
    "blog",
    "ai",
    "ai trainer",
    "ai training",
    "prompt",
    "research",
    "virtual assistant",
]


def search_job_opportunities():
    response = requests.get(
        REMOTE_OK_API,
        headers={
            "User-Agent": "Buggy-Agent/1.0"
        },
        timeout=30,
    )

    response.raise_for_status()

    jobs = response.json()

    opportunities = []

    for job in jobs:
        if not isinstance(job, dict):
            continue

        text = (
            str(job.get("position", ""))
            + " "
            + str(job.get("description", ""))
            + " "
            + " ".join(job.get("tags", []))
        ).lower()

        if not any(keyword in text for keyword in KEYWORDS):
            continue

        opportunities.append({
            "id": f"remoteok:{job.get('id')}",
            "title": job.get("position", "Untitled"),
            "company": job.get("company", "Unknown"),
            "url": job.get("url"),
            "source": "Remote OK",
            "tags": job.get("tags", []),
            "salary": job.get("salary", ""),
        })

    return opportunities
