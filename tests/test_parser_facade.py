"""Compatibility regression tests for the parser module split (Issue #14)."""
import json
import unittest

from news_engine import feed_parsers, sources


class ParserFacadeTests(unittest.TestCase):
    def test_legacy_parser_symbols_reference_new_module(self):
        self.assertIs(sources.FeedItem, feed_parsers.FeedItem)
        self.assertIs(sources.parse_rss, feed_parsers.parse_rss)
        self.assertIs(sources.parse_json_list, feed_parsers.parse_json_list)
        self.assertEqual(sources.MAX_ITEMS, feed_parsers.MAX_ITEMS)
        self.assertEqual(sources.MAX_RESPONSE_BYTES, feed_parsers.MAX_RESPONSE_BYTES)

    def test_parsing_rss_atom_json_from_legacy_facade_matches_new_module(self):
        rss = b'<rss><channel><item><title>Sample news</title><guid>x</guid></item></channel></rss>'
        atom = (b'<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
                b'<title>Sample news</title><id>x</id></entry></feed>')
        flat_json = json.dumps({"items": [{"title": "Sample news", "id": "x"}]}).encode()
        for payload in (rss, atom):
            with self.subTest(kind=payload[:15]):
                self.assertEqual(sources.parse_rss(payload, "fixture"),
                                 feed_parsers.parse_rss(payload, "fixture"))
        self.assertEqual(sources.parse_json_list(flat_json, "fixture"),
                         feed_parsers.parse_json_list(flat_json, "fixture"))

    def test_parsers_do_not_fetch(self):
        from unittest import mock
        with mock.patch("news_engine.sources.socket.getaddrinfo",
                        side_effect=AssertionError("network not allowed")):
            result = feed_parsers.parse_rss(
                b'<rss><channel><item><title>Safe</title></item></channel></rss>',
                "fixture")
        self.assertEqual(len(result), 1)

    def test_invalid_json_and_dtd_still_rejected(self):
        with self.assertRaises(ValueError):
            sources.parse_json_list(b'{not json', "fixture")
        with self.assertRaises(ValueError):
            sources.parse_rss(
                b'<!DOCTYPE rss [<!ENTITY x "X">]><rss><channel/></rss>', "fixture")


if __name__ == "__main__":
    unittest.main()
