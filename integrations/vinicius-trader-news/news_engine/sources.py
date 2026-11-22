"""Public-feed adapters and an opt-in, pinned-IP HTTPS-only fetcher.

No redirects, proxies, HTTP, localhost or private/reserved DNS results. Network
connections occur ONLY when fetch_feed()/collect() is explicitly called.
"""
from __future__ import annotations

import http.client
import ipaddress
import re
import socket
import ssl
from urllib.parse import urlsplit

from .feed_parsers import FeedItem, parse_json_list, parse_rss

# Preserve historical public constants, signatures and import paths.
# HTTP controls intentionally remain in this module to preserve monkeypatch
# injection points used in the security regression tests.

USER_AGENT = "NewsIntelligenceEngine-Public/2.0"
MAX_RESPONSE_BYTES = 2_000_000
MAX_ITEMS = 500


class FeedSecurityError(ValueError):
    pass


def validate_url(url: str) -> tuple[str, str]:
    """Allow external HTTPS on 443. Actual resolved address is checked AND pinned."""
    if not isinstance(url, str) or len(url) > 2048 or any(ord(c) < 32 or c == "\\" for c in url):
        raise FeedSecurityError("invalid URL")
    p = urlsplit(url)
    host = p.hostname
    if p.scheme.lower() != "https" or not host or p.username or p.password or p.fragment:
        raise FeedSecurityError("only HTTPS public feed URLs are allowed")
    try:
        port = p.port
    except ValueError as exc:
        raise FeedSecurityError("invalid port") from exc
    if port not in (None, 443):
        raise FeedSecurityError("only HTTPS port 443 is permitted")
    name = host.lower().rstrip(".")
    if name.endswith((".local", ".localhost", ".internal", ".test", ".invalid")) or name == "localhost":
        raise FeedSecurityError("local hostname not permitted")
    try:
        ipaddress.ip_address(name)
    except ValueError:
        pass
    else:
        raise FeedSecurityError("IP literals are not permitted")
    if len(name) > 253 or not re.fullmatch(r"[a-z0-9-]+(?:\.[a-z0-9-]+)+", name):
        raise FeedSecurityError("invalid public DNS hostname")
    return name, (p.path or "/") + ("?" + p.query if p.query else "")


def _public_addresses(host: str) -> list[str]:
    infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    addrs = sorted({info[4][0] for info in infos})
    if not addrs or not all(ipaddress.ip_address(ip).is_global for ip in addrs):
        raise FeedSecurityError("DNS target is not exclusively public")
    return addrs


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    def __init__(self, host: str, ip: str, timeout: float):
        super().__init__(host, port=443, timeout=timeout, context=ssl.create_default_context())
        self._fixed_ip = ip

    def connect(self):
        raw = socket.create_connection((self._fixed_ip, 443), self.timeout)
        try:
            # Validate TLS certificate against the original DNS name, not the IP.
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)
        except Exception:
            raw.close()
            raise


def _safe_cache_header(value: str | None) -> str | None:
    """Accept bounded, single-line ASCII HTTP validator values only."""
    if not isinstance(value, str) or not value or len(value) > 200:
        return None
    if any(ord(char) < 32 or ord(char) > 126 for char in value):
        return None
    return value


def _content_length(response, max_bytes: int) -> None:
    value = response.getheader("Content-Length")
    if value is None:
        return
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]+", value.strip()):
        raise FeedSecurityError("invalid Content-Length")
    if int(value.strip()) > max_bytes:
        raise FeedSecurityError("response exceeds configured size limit")


def fetch_feed(url: str, timeout: float = 12, max_bytes: int = MAX_RESPONSE_BYTES,
               etag: str | None = None, modified: str | None = None,
               connection_factory=None) -> tuple[bytes | None, dict]:
    """Return (bytes, metadata) or (None, metadata) for 304.

    The optional factory is for local no-network tests; never taken from feed input.
    """
    host, path = validate_url(url)
    # Never retry a response-status, certificate, parser, or header validation error.
    # Only transport failures may advance to another previously validated public IP.
    addresses = _public_addresses(host) if connection_factory is None else ["fixture-ip"]
    factory = connection_factory or PinnedHTTPSConnection
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, application/json, text/xml",
    }
    safe_etag = _safe_cache_header(etag)
    safe_modified = _safe_cache_header(modified)
    if safe_etag:
        headers["If-None-Match"] = safe_etag
    if safe_modified:
        headers["If-Modified-Since"] = safe_modified

    for index, ip in enumerate(addresses):
        connection = None
        response_received = False
        try:
            connection = factory(host, ip, float(timeout))
            connection.request("GET", path, headers=headers)
            resp = connection.getresponse()
            response_received = True
            status = int(resp.status)
            meta = {
                "status": status,
                "etag": _safe_cache_header(resp.getheader("ETag")),
                "last_modified": _safe_cache_header(resp.getheader("Last-Modified")),
            }
            if status == 304:
                return None, meta
            if status != 200:
                raise FeedSecurityError(f"HTTP response rejected: {status}")
            _content_length(resp, max_bytes)
            data = resp.read(max_bytes + 1)
            if len(data) > max_bytes:
                raise FeedSecurityError("response exceeds configured size limit")
            return data, meta
        except OSError as exc:
            # Retry only connection/transport errors before an HTTP response exists.
            # TLS authentication, HTTP responses and body-read failures fail closed.
            if isinstance(exc, ssl.SSLError) or response_received or index == len(addresses) - 1:
                raise
        finally:
            if connection is not None:
                connection.close()
    raise FeedSecurityError("no validated address available")

def collect(feeds, *, cache_get=None, cache_put=None, fetcher=None) -> tuple[list[FeedItem], list[dict]]:
    """Retrieve configured public feeds; unchanged HTTP 304 is not an error."""
    items, errors = [], []
    fetcher = fetcher or fetch_feed
    for feed in feeds or []:
        name = str(feed.get("name") or "feed")
        url = feed.get("url")
        if not url:
            continue
        state = cache_get(url) if cache_get else {}
        state = state or {}
        try:
            data, meta = fetcher(url, etag=state.get("etag"), modified=state.get("last_modified"))
            if cache_put:
                cache_put(url, meta)
            if data is None:
                continue
            kind = str(feed.get("format", "xml")).lower()
            if kind in ("rss", "atom", "xml"):
                items.extend(parse_rss(data, name))
            elif kind == "json":
                items.extend(parse_json_list(data, name, list_key=feed.get("list_key", "items"),
                                             fields=feed.get("fields")))
            else:
                raise ValueError("unsupported feed format")
        except Exception as exc:
            errors.append({"source": name, "error": f"{type(exc).__name__}: {exc}"})
    return items, errors
