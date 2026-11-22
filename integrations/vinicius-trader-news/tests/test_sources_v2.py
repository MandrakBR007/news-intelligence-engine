import json
import unittest
from unittest import mock

from news_engine import sources


ATOM = b"""<?xml version='1.0'?>
<feed xmlns='http://www.w3.org/2005/Atom'><entry>
<title>Sample Economic Update</title><id>article-1</id><link href='https://example.org/article'/>
<summary>Test item</summary><published>2026-01-01T12:00:00Z</published>
</entry></feed>"""


class FakeResponse:
    def __init__(self, status=200, body=b"ok", headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}
    def getheader(self, key):
        return self.headers.get(key)
    def read(self, count):
        return self.body[:count]


class FakeConnection:
    next_response = None
    last_request = None
    def __init__(self, host, address, timeout):
        self.host, self.address, self.timeout = host, address, timeout
    def request(self, method, path, headers=None):
        FakeConnection.last_request = (method, path, headers)
    def getresponse(self):
        return self.next_response
    def close(self):
        return None


class SourcesV2Tests(unittest.TestCase):
    def test_parse_atom(self):
        items = sources.parse_rss(ATOM, "demo")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].external_id, "article-1")
        self.assertTrue(items[0].published_at.startswith("2026-01-01T12:00:00"))

    def test_parse_json_with_mapping_and_missing_date(self):
        raw = json.dumps({"entries": [{"headline": "Synthetic GDP release", "id": "x"}]}).encode()
        result = sources.parse_json_list(raw, "demo", list_key="entries",
                                         fields={"title": "headline", "external_id": "id"})
        self.assertEqual(result[0].external_id, "x")
        self.assertIsNone(result[0].published_at)

    def test_disallowed_urls(self):
        for url in ("file:///etc/passwd", "http://example.org/rss", "https://127.0.0.1/",
                    "https://localhost/news", "https://user:pass@example.org/feed",
                    "https://example.org:123/feed", "https://example.org\\@evil.org/"):
            with self.subTest(url=url), self.assertRaises(sources.FeedSecurityError):
                sources.validate_url(url)

    @mock.patch("news_engine.sources.socket.getaddrinfo")
    def test_rejects_private_dns(self, ga):
        ga.return_value = [(2, 1, 6, "", ("127.0.0.1", 443))]
        with self.assertRaises(sources.FeedSecurityError):
            sources._public_addresses("example.org")

    def test_limited_body_and_no_redirect(self):
        FakeConnection.next_response = FakeResponse(200, b"123456")
        with self.assertRaises(sources.FeedSecurityError):
            sources.fetch_feed("https://example.org/news", max_bytes=4, connection_factory=FakeConnection)
        FakeConnection.next_response = FakeResponse(302, b"")
        with self.assertRaises(sources.FeedSecurityError):
            sources.fetch_feed("https://example.org/news", connection_factory=FakeConnection)

    def test_conditional_fetch_304(self):
        FakeConnection.next_response = FakeResponse(304, b"", {"ETag": '"etag2"'})
        body, meta = sources.fetch_feed("https://example.org/news", etag='"etag1"',
                                        connection_factory=FakeConnection)
        self.assertIsNone(body)
        self.assertEqual(meta["status"], 304)
        self.assertEqual(FakeConnection.last_request[2]["If-None-Match"], '"etag1"')

    def test_rejects_large_xml(self):
        with self.assertRaises(ValueError):
            sources.parse_rss(b"a" * (sources.MAX_RESPONSE_BYTES + 1), "demo")


if __name__ == "__main__":
    unittest.main()
