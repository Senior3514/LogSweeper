"""HTTP pull connector for LogSweeper - fetches logs from remote HTTP endpoints."""

import ipaddress
import logging
import socket
import urllib.request
import urllib.error
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Maximum response size (5 MB)
MAX_RESPONSE_SIZE = 5 * 1024 * 1024

# Blocked private/internal IP ranges for SSRF prevention
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local / cloud metadata
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
]


def _is_url_safe(url: str) -> bool:
    """Validate that a URL does not target internal/private networks."""
    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    hostname = parsed.hostname
    if not hostname:
        return False

    # Block common internal hostnames
    blocked_hosts = {"localhost", "metadata.google.internal", "169.254.169.254"}
    if hostname.lower() in blocked_hosts:
        return False

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port or 443)
        for family, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            for network in _BLOCKED_NETWORKS:
                if ip in network:
                    return False
    except (socket.gaierror, ValueError):
        return False

    return True


def pull_logs(url: str, timeout: int = 30) -> list[str]:
    """Fetch log lines from a remote HTTP endpoint with SSRF protection."""
    if not _is_url_safe(url):
        logger.warning("Blocked SSRF attempt to internal URL: %s", url)
        raise PermissionError("URL targets a blocked internal network")

    try:
        req = urllib.request.Request(url)
        req.add_header("User-Agent", "LogSweeper/0.1.0")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read(MAX_RESPONSE_SIZE)
            if response.read(1):
                logger.warning("Response from %s exceeded max size, truncated", url)
            return body.decode("utf-8", errors="replace").splitlines()
    except urllib.error.URLError as e:
        logger.error("Failed to pull logs from %s: %s", url, e)
        return []
    except Exception as e:
        logger.error("Unexpected error pulling from %s: %s", url, e)
        return []
