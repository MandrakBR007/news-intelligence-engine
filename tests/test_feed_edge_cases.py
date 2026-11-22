"""Offline parser edge-case contracts for Issue #6.

All payloads are synthetic; no network, credentials or third-party content.
"""
import json
import unittest
import xml.etree.ElementTree as ET

from news_engine.feed_parsers import (
    MAX_ITEMS,
    MAX_RESPONSE_BYTES,
    parse_json_list,
    parse_rss,
)


class FeedEdgeCaseTests(unittest.TestCase):
    def test_rss_skips_missing_title_but_keeps_empty_summary(self):
        payload = (b"<rss><channel>"
                   b"<item><guid>missing</guid><description>Ignored</description></item>"
                   b"<item><guid>keep</guid><title>  News   item  </title></item>"
                   b"</channel></rss>")
        items = parse_rss(payload, "fixture")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].external_id, "keep")
        self.assertEqual(items[0].title, "News item")
        self.assertEqual(items[0].summary, "")
        self.assertIsNone(items[0].published_at)

    def test_atom_missing_title_and_invalid_date(self):
        payload = (b'<feed xmlns="http://www.w3.org/2005/Atom">'
                   b"<entry><id>no-title</id></entry>"
                   b"<entry><id>valid</id><title>Sample update</title>"
                   b"<published>not a date</published></entry></feed>")
        items = parse_rss(payload, "fixture")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].external_id, "valid")
        self.assertIsNone(items[0].published_at)

    def test_rss_invalid_date_stays_unknown(self):
        payload = (b"<rss><channel><item><title>Sample</title>"
                   b"<pubDate>not-a-timestamp</pubDate></item></channel></rss>")
        self.assertIsNone(parse_rss(payload, "fixture")[0].published_at)

    def test_duplicate_external_ids_are_not_silently_collapsed_by_parsers(self):
        rss = (b"<rss><channel>"
               b"<item><guid>same</guid><title>Revision one</title></item>"
               b"<item><guid>same</guid><title>Revision two</title></item>"
               b"</channel></rss>")
        atom = (b'<feed xmlns="http://www.w3.org/2005/Atom">'
                b"<entry><id>same</id><title>Revision one</title></entry>"
                b"<entry><id>same</id><title>Revision two</title></entry></feed>")
        json_payload = json.dumps({"items": [
            {"external_id": "same", "title": "Revision one"},
            {"external_id": "same", "title": "Revision two"},
        ]}).encode()
        for parsed in (parse_rss(rss, "fixture"), parse_rss(atom, "fixture"),
                       parse_json_list(json_payload, "fixture")):
            with self.subTest(format=type(parsed[0]).__name__):
                self.assertEqual([item.external_id for item in parsed], ["same", "same"])
                self.assertNotEqual(parsed[0].title, parsed[1].title)

    def test_json_skips_non_objects_and_missing_titles(self):
        payload = json.dumps({"items": [None, 5, "not an object",
            {"external_id": "missing", "summary": "No title"},
            {"external_id": "ok", "title": " Hello  world ", "summary": ""},
        ]}).encode()
        items = parse_json_list(payload, "fixture")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "Hello world")
        self.assertEqual(items[0].summary, "")
        self.assertIsNone(items[0].published_at)

    def test_json_configured_field_names_and_invalid_date(self):
        payload = json.dumps({"entries": [{"headline": "Indicador divulgado",
            "id": "p1", "date": "invalid", "body": ""}]}).encode()
        items = parse_json_list(payload, "fixture", list_key="entries",
                                fields={"title": "headline", "external_id": "id",
                                        "published_at": "date", "summary": "body"})
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].external_id, "p1")
        self.assertIsNone(items[0].published_at)

    def test_malformed_xml_and_json_raise(self):
        with self.assertRaises(ET.ParseError):
            parse_rss(b"<rss><channel><item></rss>", "fixture")
        with self.assertRaises(ValueError):
            parse_json_list(b"{bad-json", "fixture")
        with self.assertRaises(ValueError):
            parse_json_list(b'{"items": {"title": "wrong shape"}}', "fixture")

    def test_dtd_and_entity_declarations_rejected(self):
        payload = (b'<!DOCTYPE rss [<!ENTITY expansion "unsafe">]>'
                   b"<rss><channel><item><title>&expansion;</title>"
                   b"</item></channel></rss>")
        with self.assertRaisesRegex(ValueError, "DTD"):
            parse_rss(payload, "fixture")

    def test_bounded_payloads_and_item_counts(self):
        with self.assertRaisesRegex(ValueError, "too large"):
            parse_rss(b"x" * (MAX_RESPONSE_BYTES + 1), "fixture")
        with self.assertRaisesRegex(ValueError, "too large"):
            parse_json_list(b"x" * (MAX_RESPONSE_BYTES + 1), "fixture")
        json_payload = json.dumps([{"title": f"Fixture {i}"} for i in
                                   range(MAX_ITEMS + 2)]).encode()
        self.assertEqual(len(parse_json_list(json_payload, "fixture")), MAX_ITEMS)
        rss = ("<rss><channel>" +
               "".join(f"<item><title>Fixture {i}</title></item>"
                       for i in range(MAX_ITEMS + 2)) +
               "</channel></rss>").encode()
        self.assertEqual(len(parse_rss(rss, "fixture")), MAX_ITEMS)

    def test_long_fields_within_payload_limit_are_preserved(self):
        title = "Synthetic headline " + ("x" * 12000)
        payload = json.dumps([{"title": title}]).encode()
        item = parse_json_list(payload, "fixture")[0]
        self.assertEqual(item.title, title)
        self.assertEqual(len(item.title), len(title))


if __name__ == "__main__":
    unittest.main()
