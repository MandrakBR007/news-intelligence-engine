"""Public-feed adapters and an opt-in, pinned-IP HTTPS-only fetcher.

No redirects, proxies, HTTP, localhost or private/reserved DNS results. Network
connections occur ONLY when fetch_feed()/collect() is explicitly called.
"""
from __future__ import annotations

import http.client
import ipaddress
import json
import re
import socket
import ssl
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from urllib.parse import urlsplit

from .util import normalize_text, parse_dt, sha256_hex

USER_AGENT = "NewsIntelligenceEngine-Public/2.0"
MAX_RESPONSE_BYTES = 2_000_000
MAX_ITEMS = 500


class FeedSecurityError(ValueError):
    pass


@dataclass
class FeedItem:
    source: str
    external_id: str
    title: str
    summary: str
    link: str
    published_at: str | None

    def as_dict(self) -> dict:
        return asdict(self)


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


def fetch_feed(url: str, timeout: float = 12, max_bytes: int = MAX_RESPONSE_BYTES,
               etag: str | None = None, modified: str | None = None,
               connection_factory=None) -> tuple[bytes | None, dict]:
    """Return (bytes, metadata) or (None, metadata) for 304.

    The optional factory is for local no-network tests; never taken from feed input.
    """
    host, path = validate_url(url)
    addresses = _public_addresses(host) if connection_factory is None else ["fixture-ip"]
    factory = connection_factory or PinnedHTTPSConnection
    connection = factory(host, addresses[0], float(timeout))
    headers = {"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/atom+xml, application/xml, application/json, text/xml"}
    if etag:
        headers["If-None-Match"] = etag[:200]
    if modified:
        headers["If-Modified-Since"] = modified[:200]
    try:
        connection.request("GET", path, headers=headers)
        resp = connection.getresponse()
        status = int(resp.status)
        meta = {"status": status, "etag": resp.getheader("ETag"),
                "last_modified": resp.getheader("Last-Modified")}
        if status == 304:
            return None, meta
        if status != 200:
            # Includes all redirects; refuse them, even across seemingly safe hosts.
            raise FeedSecurityError(f"HTTP response rejected: {status}")
        if int(resp.getheader("Content-Length") or "0") > max_bytes:
            raise FeedSecurityError("response exceeds configured size limit")
        data = resp.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise FeedSecurityError("response exceeds configured size limit")
        return data, meta
    finally:
        connection.close()


def _plain(node, name):
    n = node.find(name)
    return "" if n is None else "".join(n.itertext()).strip()


def parse_rss(xml_bytes: bytes, source: str) -> list[FeedItem]:
    """RSS 2.0 and Atom 1.0, with bounded item count."""
    if len(xml_bytes) > MAX_RESPONSE_BYTES:
        raise ValueError("feed too large")
    # Refuse DTD and entity declarations rather than processing untrusted expansions.
    xml_head = xml_bytes.upper()
    if b"<!DOCTYPE" in xml_head or b"<!ENTITY" in xml_head:
        raise ValueError("DTD and custom entities are not permitted")
    root = ET.fromstring(xml_bytes)
    if root.tag == "{http://www.w3.org/2005/Atom}feed":
        atom = "{http://www.w3.org/2005/Atom}"
        out = []
        for node in root.findall(atom + "entry")[:MAX_ITEMS]:
            title = normalize_text(_plain(node, atom + "title"))
            if not title:
                continue
            link_node = next((n for n in node.findall(atom + "link")
                              if n.attrib.get("rel", "alternate") == "alternate"), None)
            link = link_node.attrib.get("href", "") if link_node is not None else ""
            summary = normalize_text(_plain(node, atom + "summary") or _plain(node, atom + "content"))
            ext_id = _plain(node, atom + "id") or link or sha256_hex(title + summary)
            timestamp = _plain(node, atom + "published") or _plain(node, atom + "updated")
            out.append(FeedItem(source, ext_id, title, summary, link, parse_dt(timestamp)))
        return out
    channel = root.find("channel") if root.tag.lower().endswith("rss") else root
    out = []
    if channel is None:
        return out
    for node in channel.findall("item")[:MAX_ITEMS]:
        title = normalize_text(_plain(node, "title"))
        if not title:
            continue
        link = _plain(node, "link")
        summary = normalize_text(_plain(node, "description") or _plain(node, "summary"))
        ext_id = _plain(node, "guid") or link or sha256_hex(title + summary)
        timestamp = _plain(node, "pubDate") or _plain(node, "published")
        out.append(FeedItem(source, ext_id, title, summary, link, parse_dt(timestamp)))
    return out


def parse_json_list(raw: bytes, source: str, *, list_key: str = "items",
                    fields: dict | None = None) -> list[FeedItem]:
    """Generic, user-configured flat JSON list; no domain-specific extraction."""
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("feed too large")
    data = json.loads(raw)
    records = data if isinstance(data, list) else data.get(list_key, [])
    if not isinstance(records, list):
        raise ValueError("JSON list_key did not locate an array")
    fields = fields or {}
    def field(row, key):
        return row.get(fields.get(key, key)) or ""
    result = []
    for row in records[:MAX_ITEMS]:
        if not isinstance(row, dict):
            continue
        title = normalize_text(field(row, "title"))
        if not title:
            continue
        summary = normalize_text(field(row, "summary"))
        link = str(field(row, "link"))
        ext_id = str(field(row, "external_id") or link or sha256_hex(title + summary))
        result.append(FeedItem(source, ext_id, title, summary, link,
                               parse_dt(field(row, "published_at"))))
    return result


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
