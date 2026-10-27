import os
import time

import requests
from requests.exceptions import HTTPError, RequestException, Timeout


GITHUB_SEARCH_URL = "https://api.github.com/search/issues"

# Search queries are intentionally preserved exactly as before.
QUERIES = [
    "bounty is:open",
    "reward is:open",
    '"$" bounty is:open',
    "paid is:open",
]

REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 1  # one retry max; avoid hammering a rate-limited API
MAX_WAIT_SECONDS = 60  # cap any single rate-limit sleep


def _auth_headers():
    """Build headers for GitHub API requests.

    Adds ``Authorization: Bearer <token>`` only when ``GH_API_TOKEN`` is set
    in the environment. The token value is never logged or returned.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Buggy-Agent/1.0",
    }

    token = os.getenv("GH_API_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return headers


def _rate_limit_wait_seconds(response, attempt):
    """Seconds to wait before retrying a rate-limited request.

    Honors ``Retry-After`` (seconds or an HTTP date) and
    ``X-RateLimit-Reset`` (Unix timestamp) when present. Falls back to a short
    backoff. The result is capped so one sleep cannot block the run for too
    long. Returns 0 when no actionable wait time can be determined.
    """
    retry_after = response.headers.get("Retry-After")
    if retry_after:
        retry_after = retry_after.strip()
        try:
            return int(retry_after)
        except ValueError:
            try:
                import email.utils

                reset_time = email.utils.parsedate_to_datetime(retry_after)
                if reset_time is not None:
                    return max(int(reset_time.timestamp()) - int(time.time()), 0)
            except (TypeError, ValueError, OverflowError):
                pass

    reset = response.headers.get("X-RateLimit-Reset")
    if reset:
        try:
            return max(int(reset) - int(time.time()), 0)
        except ValueError:
            pass

    return min(2 ** attempt, MAX_WAIT_SECONDS)


def search_github_opportunities():
    """Search GitHub issues for bounty/reward/paid opportunities.

    Returns a list of opportunity dicts in the existing format, with
    deduplication preserved across queries.

    Authentication: uses ``GH_API_TOKEN`` from the environment as a Bearer
    token when available. Unauthenticated searches are subject to GitHub's
    stricter rate limits, which is the root cause of the ``403 rate limit
    exceeded`` failure.

    Failure behavior: on network, auth, or rate-limit failure this function
    logs a clear warning and returns whatever opportunities were collected so
    far (possibly an empty list). It never raises, so the rest of the agent
    keeps running. A failed scan is never silently reported as a successful
    empty scan.
    """
    headers = _auth_headers()
    opportunities = []
    seen = set()
    scan_failed = False

    for query in QUERIES:
        params = {
            "q": query,
            "sort": "updated",
            "order": "desc",
            "per_page": 10,
        }

        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.get(
                    GITHUB_SEARCH_URL,
                    params=params,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                )
            except Timeout as error:
                print(
                    f"⚠️ GitHub request timed out for query {query!r}: {error}"
                )
                scan_failed = True
                break
            except RequestException as error:
                print(
                    f"⚠️ GitHub request failed for query {query!r}: {error}"
                )
                scan_failed = True
                break

            # ----------------------------------------------------------
            # Rate limit (HTTP 403 / 429): back off, retry at most once.
            # ----------------------------------------------------------
            if response.status_code in (403, 429):
                wait = _rate_limit_wait_seconds(response, attempt)
                remaining = response.headers.get(
                    "X-RateLimit-Remaining", "unknown"
                )
                reset = response.headers.get("X-RateLimit-Reset", "unknown")

                if attempt < MAX_RETRIES and wait > 0:
                    print(
                        f"⚠️ GitHub API rate limited (HTTP "
                        f"{response.status_code}). Retrying in {wait}s... "
                        f"(remaining={remaining}, reset={reset})"
                    )
                    time.sleep(min(wait, MAX_WAIT_SECONDS))
                    continue

                print(
                    f"⚠️ GitHub search failed for query {query!r}: "
                    f"HTTP {response.status_code} (rate limit exceeded). "
                    f"remaining={remaining}, reset={reset}. Skipping query."
                )
                scan_failed = True
                break

            try:
                response.raise_for_status()
            except HTTPError as error:
                print(
                    f"⚠️ GitHub search failed for query {query!r}: {error}"
                )
                scan_failed = True
                break

            try:
                data = response.json()
            except ValueError as error:
                print(
                    f"⚠️ GitHub search returned invalid JSON for query "
                    f"{query!r}: {error}"
                )
                scan_failed = True
                break

            for item in data.get("items", []):
                opportunity_id = item["html_url"]

                if opportunity_id in seen:
                    continue

                seen.add(opportunity_id)

                opportunities.append(
                    {
                        "id": opportunity_id,
                        "title": item["title"],
                        "html_url": item["html_url"],
                        "source": "GitHub",
                        "reward": extract_reward(item["title"]),
                    }
                )

            break  # move to the next query

    if scan_failed:
        print(
            "⚠️ Warning: GitHub opportunity scan failed or was rate limited. "
            "GitHub results may be incomplete; continuing with other sources."
        )

    return opportunities


def extract_reward(title):
    import re

    match = re.search(r"\$\s?[\d,]+(?:\.\d+)?", title)

    if match:
        return match.group(0)

    return "Not specified"
