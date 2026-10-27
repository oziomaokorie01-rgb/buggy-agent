import os
import sys
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import requests
from requests.exceptions import ConnectionError, HTTPError, Timeout

import scanner


def _make_response(status_code=200, items=None, headers=None):
    """Build a fake requests.Response-like object."""
    response = MagicMock()
    response.status_code = status_code
    response.headers = headers or {}
    response.json.return_value = {"items": items or []}

    def _raise_for_status():
        if 400 <= status_code < 600:
            error = HTTPError(f"HTTP {status_code}")
            error.response = response
            raise error

    response.raise_for_status = _raise_for_status
    return response


class _EnvVar:
    """Temporarily set or remove GH_API_TOKEN, restoring it on exit."""

    def __init__(self, value=None):
        self.value = value
        self.previous = None

    def __enter__(self):
        self.previous = os.environ.get("GH_API_TOKEN")
        if self.value is None:
            os.environ.pop("GH_API_TOKEN", None)
        else:
            os.environ["GH_API_TOKEN"] = self.value
        return self

    def __exit__(self, *exc_info):
        if self.previous is None:
            os.environ.pop("GH_API_TOKEN", None)
        else:
            os.environ["GH_API_TOKEN"] = self.previous


class TestGitHubScannerAuth(unittest.TestCase):
    @patch("scanner.time.sleep", return_value=None)
    def test_bearer_header_sent_when_token_set(self, mock_sleep):
        with _EnvVar("test-token-123"), patch(
            "scanner.requests.get"
        ) as mock_get:
            mock_get.return_value = _make_response(
                200,
                items=[
                    {
                        "html_url": "https://github.com/o/repo/issues/1",
                        "title": "$100 bounty",
                    }
                ],
            )

            result = scanner.search_github_opportunities()

            self.assertEqual(len(result), 1)
            kwargs = mock_get.call_args.kwargs
            self.assertEqual(
                kwargs["headers"]["Authorization"], "Bearer test-token-123"
            )
            self.assertEqual(kwargs["timeout"], scanner.REQUEST_TIMEOUT)

    @patch("scanner.time.sleep", return_value=None)
    def test_no_auth_header_when_token_missing(self, mock_sleep):
        with _EnvVar(None), patch("scanner.requests.get") as mock_get:
            mock_get.return_value = _make_response(200, items=[])

            scanner.search_github_opportunities()

            headers = mock_get.call_args.kwargs["headers"]
            self.assertNotIn("Authorization", headers)


class TestGitHubScannerRateLimit(unittest.TestCase):
    @patch("scanner.time.sleep", return_value=None)
    def test_429_retry_then_success(self, mock_sleep):
        with _EnvVar("tok"), patch("scanner.requests.get") as mock_get:
            rate_limited = _make_response(
                429,
                items=[],
                headers={
                    "Retry-After": "1",
                    "X-RateLimit-Remaining": "0",
                },
            )
            ok = _make_response(
                200,
                items=[
                    {
                        "html_url": "https://github.com/o/repo/issues/2",
                        "title": "$50 reward",
                    }
                ],
            )
            # Query 1: 429 then 200 (2 calls). Queries 2-4: 200 each (1 call).
            mock_get.side_effect = [rate_limited, ok, ok, ok, ok]

            result = scanner.search_github_opportunities()

            # Query 1: 429 then 200 (2 calls). Queries 2-4: 200 each (1 call).
            self.assertEqual(mock_get.call_count, 5)
            mock_sleep.assert_called_once_with(1)
            # All queries return the same item; dedup collapses to one.
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["title"], "$50 reward")

    @patch("scanner.time.sleep", return_value=None)
    def test_persistent_403_returns_empty_without_raising(self, mock_sleep):
        with _EnvVar("tok"), patch("scanner.requests.get") as mock_get:
            rate_limited = _make_response(
                403,
                items=[],
                headers={
                    "X-RateLimit-Remaining": "0",
                    # Reset in the past -> wait == 0 -> give up without retry.
                    "X-RateLimit-Reset": "0",
                },
            )
            # One 403 per query, giving up each time (wait == 0).
            mock_get.side_effect = [rate_limited] * len(scanner.QUERIES)

            with patch("sys.stdout", new_callable=StringIO) as stdout:
                result = scanner.search_github_opportunities()
                output = stdout.getvalue()

            self.assertEqual(result, [])
            mock_sleep.assert_not_called()
            self.assertIn("rate limit exceeded", output)
            self.assertIn(
                "Warning: GitHub opportunity scan failed", output
            )
            # Token must not leak into logs/output.
            self.assertNotIn("tok", output)

    @patch("scanner.time.sleep", return_value=None)
    def test_network_error_does_not_raise(self, mock_sleep):
        with _EnvVar("tok"), patch("scanner.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("DNS failure")

            with patch("sys.stdout", new_callable=StringIO) as stdout:
                result = scanner.search_github_opportunities()
                output = stdout.getvalue()

            self.assertEqual(result, [])
            self.assertIn("GitHub request failed", output)
            self.assertIn(
                "Warning: GitHub opportunity scan failed", output
            )


class TestGitHubScannerDedupAndFormat(unittest.TestCase):
    @patch("scanner.time.sleep", return_value=None)
    def test_dedup_across_queries(self, mock_sleep):
        with _EnvVar(None), patch("scanner.requests.get") as mock_get:
            item = {
                "html_url": "https://github.com/o/repo/issues/1",
                "title": "$100 bounty",
            }
            # All four queries return the same item.
            mock_get.return_value = _make_response(200, items=[item])

            result = scanner.search_github_opportunities()

            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["id"], item["html_url"])
            self.assertEqual(result[0]["source"], "GitHub")
            # extract_reward extracts the numeric portion only.
            self.assertEqual(result[0]["reward"], "$100")


if __name__ == "__main__":
    unittest.main()