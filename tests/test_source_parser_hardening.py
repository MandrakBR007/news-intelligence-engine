"""Offline regression cases for hardened source and parser contracts."""
import json
import socket
import ssl
import unittest
from unittest import mock

from news_engine import sources
from news_engine.feed_parsers import parse_json_list, parse_rss


class Response:
    def __init__(self, status=200, body=b"ok", headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}

    def getheader(self, name):
        return self.headers.get(name)

    def read(self, amount):
        return self.body[:amount]


class Connection:
    def __init__(self, host, ip, timeout):
        self.host, self.ip, self.timeout = host, ip, timeout
        self.closed = False
        self.request_headers = None

    def request(self, method, path, headers=None):
        self.request_headers = headers

    def getresponse(self):
        return Response()

    def close(self):
        self.closed = True


class SourceParserHardeningTests(unittest.TestCase):
    def test_malformed_length_rejected_as_security_error_and_connection_closed(self):
        for content_length in ("100, 100", "garbage", "-1", "3.5"):
            instances = []

            def make(host, ip, timeout):
                instance = Connection(host, ip, timeout)
                instance.getresponse = lambda: Response(headers={"Content-Length": content_length})
                instances.append(instance)
                return instance

            with self.subTest(length=content_length):
                with self.assertRaises(sources.FeedSecurityError):
                    sources.fetch_feed("https://news.example.org/feed", connection_factory=make)
                self.assertTrue(instances[0].closed)

    def test_header_validators_ignore_controls_and_oversize(self):
        instance = Connection("news.example.org", "fixture-ip", 12)
        instance.getresponse = lambda: Response(headers={
            "ETag": "injected\r\nHeader: yes",
            "Last-Modified": "yesterday\nnext",
        })
        with mock.patch("news_engine.sources.PinnedHTTPSConnection", return_value=instance):
            data, metadata = sources.fetch_feed(
                "https://news.example.org/feed",
                etag="evil\r\nInjected: 1",
                modified="old\nheader",
                connection_factory=lambda *args: instance,
            )
        self.assertEqual(data, b"ok")
        self.assertNotIn("If-None-Match", instance.request_headers)
        self.assertNotIn("If-Modified-Since", instance.request_headers)
        self.assertIsNone(metadata["etag"])
        self.assertIsNone(metadata["last_modified"])
        self.assertTrue(instance.closed)

    def test_safe_cache_headers_preserved(self):
        conn = Connection("news.example.org", "fixture-ip", 12)
        conn.getresponse = lambda: Response(304, b"", {
            "ETag": 'W/"2026-v4"',
            "Last-Modified": "Sun, 22 Nov 2026 12:00:00 GMT",
        })
        body, meta = sources.fetch_feed(
            "https://news.example.org/feed",
            etag='W/"previous"',
            modified="yesterday",
            connection_factory=lambda *args: conn,
        )
        self.assertIsNone(body)
        self.assertEqual(meta["etag"], 'W/"2026-v4"')
        self.assertEqual(conn.request_headers["If-None-Match"], 'W/"previous"')
        self.assertTrue(conn.closed)

    def test_transport_failure_falls_back_to_next_vetted_ip(self):
        connections = []

        class Failing(Connection):
            def request(self, method, path, headers=None):
                super().request(method, path, headers=headers)
                if self.ip == "8.8.8.8":
                    raise OSError("synthetic connection failed")

        def factory(*args):
            conn = Failing(*args)
            connections.append(conn)
            return conn

        with mock.patch.object(sources, "_public_addresses", return_value=["8.8.8.8", "9.9.9.9"]),              mock.patch.object(sources, "PinnedHTTPSConnection", side_effect=factory):
            data, _ = sources.fetch_feed("https://news.example.org/feed")
        self.assertEqual(data, b"ok")
        self.assertEqual([c.ip for c in connections], ["8.8.8.8", "9.9.9.9"])
        self.assertTrue(all(c.closed for c in connections))

    def test_tls_failure_does_not_fallback(self):
        connections = []

        class TlsFailure(Connection):
            def request(self, method, path, headers=None):
                raise ssl.SSLError("synthetic certificate failure")

        def factory(*args):
            conn = TlsFailure(*args)
            connections.append(conn)
            return conn

        with mock.patch.object(sources, "_public_addresses", return_value=["8.8.8.8", "9.9.9.9"]),              mock.patch.object(sources, "PinnedHTTPSConnection", side_effect=factory):
            with self.assertRaises(ssl.SSLError):
                sources.fetch_feed("https://news.example.org/feed")
        self.assertEqual(len(connections), 1)
        self.assertTrue(connections[0].closed)

    def test_http_failure_does_not_fallback(self):
        connections = []
        def factory(*args):
            conn = Connection(*args)
            conn.getresponse = lambda: Response(302, b"")
            connections.append(conn)
            return conn
        with mock.patch.object(sources, "_public_addresses", return_value=["8.8.8.8", "9.9.9.9"]),              mock.patch.object(sources, "PinnedHTTPSConnection", side_effect=factory):
            with self.assertRaises(sources.FeedSecurityError):
                sources.fetch_feed("https://news.example.org/feed")
        self.assertEqual(len(connections), 1)
        self.assertTrue(connections[0].closed)

    def test_json_scalar_roots_rejected_predictably(self):
        for raw in (b"null", b"123", b'"ok"', b"true"):
            with self.subTest(raw=raw), self.assertRaisesRegex(ValueError, "JSON root"):
                parse_json_list(raw, "fixture")

    def test_json_nested_fields_not_stringified(self):
        raw = json.dumps({"items": [
            {"title": {"rendered": "Hello"}, "summary": "ignored"},
            {"title": "Valid headline", "summary": {"rendered": "hidden"},
             "published_at": {"value": "2026-01-01"}, "external_id": ["not", "scalar"]},
        ]}).encode()
        items = parse_json_list(raw, "fixture")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Valid headline")
        self.assertEqual(items[0].summary, "")
        self.assertNotIn("{", items[0].external_id)
        self.assertIsNone(items[0].published_at)

    def test_common_rss_namespace_fallbacks(self):
        payload = (b'<rss xmlns:dc="http://purl.org/dc/elements/1.1/" '
                   b'xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
                   b'<item><title>News update</title><description></description>'
                   b'<content:encoded>Extended summary</content:encoded>'
                   b'<dc:date>2026-11-22T12:00:00Z</dc:date></item></channel></rss>')
        items = parse_rss(payload, "fixture")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].summary, "Extended summary")
        self.assertEqual(items[0].published_at, "2026-11-22T12:00:00+00:00")

    def test_primary_rss_fields_take_precedence(self):
        payload = (b'<rss xmlns:dc="http://purl.org/dc/elements/1.1/" '
                   b'xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>'
                   b'<item><title>News</title><description>Primary</description>'
                   b'<content:encoded>Fallback</content:encoded>'
                   b'<pubDate>Sun, 22 Nov 2026 12:00:00 GMT</pubDate>'
                   b'<dc:date>2020-01-01T00:00:00Z</dc:date>'
                   b'</item></channel></rss>')
        item = parse_rss(payload, "fixture")[0]
        self.assertEqual(item.summary, "Primary")
        self.assertEqual(item.published_at, "2026-11-22T12:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
