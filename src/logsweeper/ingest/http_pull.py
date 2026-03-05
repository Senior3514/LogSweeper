"""HTTP pull connector for LogSweeper - fetches logs from remote HTTP endpoints."""

import logging
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)


def pull_logs(url: str, timeout: int = 30) -> list[str]:
    """Fetch log lines from a remote HTTP endpoint."""
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            return body.splitlines()
    except urllib.error.URLError as e:
        logger.error("Failed to pull logs from %s: %s", url, e)
        return []
    except Exception as e:
        logger.error("Unexpected error pulling from %s: %s", url, e)
        return []
