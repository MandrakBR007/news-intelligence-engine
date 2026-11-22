"""Offline regression contracts for public feed adapters and HTTPS safety."""
import json
import socket
import unittest
from unittest import mock

from news_engine import sources


class Response:
    def __init__(self, status=200, body=b"", headers=None):
        self.status = status
        self.body = body
        self.headers = headers or {}
    def getheader(self, key):
        return self.headers.get(key)
    def read(self, count):
        return self.body[:count]


class Connection:
    response = None
    request_args = None
    close_calls = 0

    def __init__(self, host, ip, timeout):
        self.host, self.ip, self.timeout = host, ip, timeout

    def request(self, method, path, headers=None):
        type(self).request_args = (method, path, headers)

    def getresponse(self):
        return type(self).response

    def close(self):
        type(self).close_calls += 1


class SecurityContractTests(unittest.TestCase):
    def test_url_rejects_ssrf_forms(self):
        rejected = [
            "http://example.org/x", "file:///etc/passwd", "https://127.0.0.1/x",
            "https://[::1]/", "https://localhost/", "https://x.internal/",
            "https://a.local/", "https://a.test/", "https://a.invalid/",
            "https://user:pass@example.org/x", "https://example.org:444/x",
            "https://example.org/path#fragment", "https://example.org/\\evil",
            "https://example.org/\nheader", "https://example.org/" + "a" * 2100,
        ]
        for url in rejected:
            with self.subTest(url=url[:60]), self.assertRaises(sources.FeedSecurityError):
                sources.validate_url(url)

    def test_url_accepts_path_query_without_auth(self):
        host, path = sources.validate_url("https://news.example.org:443/items?q=synthetic")
        self.assertEqual(host, "news.example.org")
        self.assertEqual(path, "/items?q=synthetic")

    @mock.patch("news_engine.sources.socket.getaddrinfo")
    def test_mixed_public_and_private_dns_fails_closed(self, resolved):
        resolved.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.1.2.3", 443)),
        ]
        with self.assertRaises(sources.FeedSecurityError):
            sources._public_addresses("news.example.org")

    @mock.patch("news_engine.sources.socket.getaddrinfo")
    def test_dns_only_public_addresses_allowed(self, resolved):
        resolved.return_value = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
        ]
        self.assertEqual(sources._public_addresses("news.example.org"), ["8.8.8.8"])

    def test_pinned_connection_uses_fixed_ip_and_original_tls_hostname(self):
        raw = mock.Mock()
        wrapped = mock.Mock()
        context = mock.Mock()
        context.wrap_socket.return_value = wrapped
        with mock.patch("news_engine.sources.ssl.create_default_context", return_value=context):
            conn = sources.PinnedHTTPSConnection("news.example.org", "8.8.8.8", 2.0)
            with mock.patch("news_engine.sources.socket.create_connection", return_value=raw) as dial:
                conn.connect()
        dial.assert_called_once_with(("8.8.8.8", 443), 2.0)
        context.wrap_socket.assert_called_once_with(raw, server_hostname="news.example.org")
        self.assertIs(conn.sock, wrapped)

    def test_pinned_connection_closes_raw_socket_on_tls_failure(self):
        raw = mock.Mock()
        context = mock.Mock()
        context.wrap_socket.side_effect = ValueError("synthetic TLS failure")
        with mock.patch("news_engine.sources.ssl.create_default_context", return_value=context):
            conn = sources.PinnedHTTPSConnection("news.example.org", "8.8.8.8", 2.0)
            with mock.patch("news_engine.sources.socket.create_connection", return_value=raw):
                with self.assertRaises(ValueError):
                    conn.connect()
        raw.close.assert_called_once()

    def test_http_redirect_and_oversize_refused_with_close(self):
        for response, limit in [
            (Response(302), 20), (Response(200, b"123456"), 4),
            (Response(200, b"", {"Content-Length": "1000"}), 4),
        ]:
            Connection.response = response
            before = Connection.close_calls
            with self.subTest(response=response.status, limit=limit):
                with self.assertRaises(sources.FeedSecurityError):
                    sources.fetch_feed("https://news.example.org/x", max_bytes=limit,
                                       connection_factory=Connection)
                self.assertEqual(Connection.close_calls, before + 1)

    def test_304_preserves_conditional_headers(self):
        Connection.response = Response(304, b"", {"ETag": "v2"})
        data, meta = sources.fetch_feed(
            "https://news.example.org/x", etag="v1", modified="yesterday",
            connection_factory=Connection)
        self.assertIsNone(data)
        self.assertEqual(meta["status"], 304)
        self.assertEqual(Connection.request_args[2]["If-None-Match"], "v1")
        self.assertEqual(Connection.request_args[2]["If-Modified-Since"], "yesterday")

    def test_dtd_entity_rejected(self):
        for payload in [
            b'<!DOCTYPE rss [<!ENTITY x "value">]><rss><channel/></rss>',
            b'<!ENTITY x "unsafe"><rss><channel/></rss>',
        ]:
            with self.assertRaises(ValueError):
                sources.parse_rss(payload, "synthetic")

    def test_bounded_rss_atom_json_and_empty_titles(self):
        rss = b'<rss><channel><item><title>Example</title></item><item><link>x</link></item></channel></rss>'
        self.assertEqual(len(sources.parse_rss(rss, "synthetic")), 1)
        atom = (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
                b'<title>Example</title><id>1</id></entry></feed>')
        self.assertEqual(len(sources.parse_rss(atom, "synthetic")), 1)
        payload = json.dumps({"items": [{"title": "Example"}, {"title": ""}]}).encode()
        self.assertEqual(len(sources.parse_json_list(payload, "synthetic")), 1)

    def test_compatibility_imports_remain_callable(self):
        for name in ("FeedItem", "FeedSecurityError", "parse_rss", "parse_json_list",
                     "collect", "fetch_feed", "validate_url"):
            self.assertTrue(hasattr(sources, name), name)


if __name__ == "__main__":
    unittest.main()
