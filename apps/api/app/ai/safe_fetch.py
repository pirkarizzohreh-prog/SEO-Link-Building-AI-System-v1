"""Fetches a competitor page's HTML with basic SSRF safeguards.

Any authenticated user can register a `competitor_page` URL that this
code then fetches server-side — a classic SSRF vector (pointing it at
http://169.254.169.254/, http://localhost:..., an internal service,
etc.). This is not a general-purpose hardened fetcher (no DNS-rebind
protection between the check and the request, no redirect-chain
re-validation beyond httpx's own redirect handling), but it blocks the
easy cases; revisit if this tool is ever exposed beyond a trusted
internal team.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

import httpx

MAX_RESPONSE_BYTES = 2 * 1024 * 1024  # 2MB
FETCH_TIMEOUT_SECONDS = 10.0


class UnsafeUrlError(ValueError):
    pass


def _is_public_ip(ip_str: str) -> bool:
    ip = ipaddress.ip_address(ip_str)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _assert_safe_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeUrlError(f"Unsupported URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise UnsafeUrlError("URL has no hostname")

    try:
        resolved = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve host {parsed.hostname!r}: {exc}") from exc

    for family, _, _, _, sockaddr in resolved:
        ip_str = sockaddr[0]
        if not _is_public_ip(ip_str):
            raise UnsafeUrlError(f"Refusing to fetch {url!r}: resolves to a non-public address ({ip_str})")


def fetch_html(url: str) -> str:
    _assert_safe_url(url)
    with httpx.Client(follow_redirects=True, timeout=FETCH_TIMEOUT_SECONDS) as http_client:
        with http_client.stream("GET", url, headers={"User-Agent": "SEOLinkBuildingBot/1.0"}) as response:
            response.raise_for_status()
            # httpx already re-validates redirect targets against the
            # same client per-request, but does not re-run our SSRF
            # check on the final URL if it differs from the input.
            if str(response.url) != url:
                _assert_safe_url(str(response.url))

            chunks: list[bytes] = []
            total = 0
            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_RESPONSE_BYTES:
                    raise UnsafeUrlError(f"Response from {url!r} exceeded {MAX_RESPONSE_BYTES} bytes")
                chunks.append(chunk)
            return b"".join(chunks).decode(response.encoding or "utf-8", errors="replace")
