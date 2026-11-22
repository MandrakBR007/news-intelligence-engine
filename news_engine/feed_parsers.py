"""Bounded, offline RSS/Atom/JSON parsers with no network access.

Extracted from sources.py without changing parsing semantics. Public imports are
still available from news_engine.sources for compatibility.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass

from .util import normalize_text, parse_dt_details, sha256_hex

MAX_RESPONSE_BYTES = 2_000_000
MAX_ITEMS = 500
DC_DATE = "{http://purl.org/dc/elements/1.1/}date"
CONTENT_ENCODED = "{http://purl.org/rss/1.0/modules/content/}encoded"


@dataclass
class FeedItem:
    source: str
    external_id: str
    title: str
    summary: str
    link: str
    published_at: str | None
    published_quality: str | None = None

    def as_dict(self) -> dict:
        return asdict(self)


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
            published_at, quality = parse_dt_details(timestamp)
            out.append(FeedItem(source, ext_id, title, summary, link,
                                published_at, quality))
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
        summary = normalize_text(_plain(node, "description") or _plain(node, "summary")
                                 or _plain(node, CONTENT_ENCODED))
        ext_id = _plain(node, "guid") or link or sha256_hex(title + summary)
        timestamp = (_plain(node, "pubDate") or _plain(node, "published")
                     or _plain(node, DC_DATE))
        published_at, quality = parse_dt_details(timestamp)
        out.append(FeedItem(source, ext_id, title, summary, link,
                            published_at, quality))
    return out


def parse_json_list(raw: bytes, source: str, *, list_key: str = "items",
                    fields: dict | None = None) -> list[FeedItem]:
    """Generic, user-configured flat JSON list; no domain-specific extraction."""
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("feed too large")
    data = json.loads(raw)
    if not isinstance(data, (list, dict)):
        raise ValueError("JSON root must be an object or array")
    records = data if isinstance(data, list) else data.get(list_key, [])
    if not isinstance(records, list):
        raise ValueError("JSON list_key did not locate an array")
    fields = fields or {}
    def field(row, key):
        value = row.get(fields.get(key, key))
        # This generic adapter handles flat JSON metadata only.
        # Never stringify nested objects into headline or provenance fields.
        return value if isinstance(value, (str, int, float)) and not isinstance(value, bool) else ""
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
        published_at, quality = parse_dt_details(field(row, "published_at"))
        result.append(FeedItem(source, ext_id, title, summary, link,
                               published_at, quality))
    return result


