import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from news_engine import dashboard, store


class DashboardAlertTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.conn = store.connect(Path(temp.name) / "news.db")
        self.addCleanup(self.conn.close)
        store.init_db(self.conn)
        self.now = datetime(2026, 11, 22, 12, 0, tzinfo=timezone.utc)

    def add_item(self, source, item_id, observed_at, *, topic="economic_data", title=None):
        timestamp = observed_at.isoformat()
        title = title or f"Headline {item_id}"
        rec = {
            "content_hash": f"hash-{item_id}",
            "cluster_id": f"cluster-{item_id}",
            "source": source,
            "external_id": str(item_id),
            "title": title,
            "summary": "Synthetic report.",
            "link": f"https://example.org/{item_id}",
            "published_at": timestamp,
            "first_seen_at": timestamp,
            "topic": topic,
            "impact": "medium",
            "confidence": 0.4,
            "status": "new",
            "simhash": item_id,
            "ingested_at": timestamp,
            "classified_at": timestamp,
        }
        store.insert_item(self.conn, rec)
        store.add_revision(self.conn, rec)
        return rec

    def test_counts_unique_sources_and_exact_duplicate_revision(self):
        seen = self.now - timedelta(minutes=5)
        first = self.add_item("Site A", 1, seen)
        self.add_item("Site A", 2, seen + timedelta(minutes=1))
        second = dict(first, source="Site B", external_id="copy-b",
                      first_seen_at=(seen + timedelta(minutes=2)).isoformat())
        store.add_revision(self.conn, second)

        alerts = dashboard.topic_alerts(self.conn, now=self.now)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["source_count"], 2)
        self.assertEqual(alerts[0]["severity"], "yellow")
        self.assertEqual({source["source"] for source in alerts[0]["sources"]},
                         {"Site A", "Site B"})
        self.assertEqual(store.distinct_source_count(self.conn), 2)
        self.assertEqual(store.recent_news_count(
            self.conn, (self.now - timedelta(minutes=30)).isoformat(),
            self.now.isoformat()), 2)

    def test_three_sources_turn_red_and_fourth_does_not_restart_timer(self):
        self.add_item("Site A", 1, self.now - timedelta(minutes=10))
        self.add_item("Site B", 2, self.now - timedelta(minutes=7))
        self.add_item("Site C", 3, self.now - timedelta(minutes=5))
        self.add_item("Site D", 4, self.now - timedelta(minutes=2))

        alert = dashboard.topic_alerts(self.conn, now=self.now)[0]

        self.assertEqual(alert["source_count"], 4)
        self.assertEqual(alert["severity"], "red")
        self.assertEqual(alert["red_since"], self.now - timedelta(minutes=5))
        self.assertEqual(alert["red_until"], self.now + timedelta(minutes=25))

    def test_observations_older_than_window_do_not_create_alerts(self):
        self.add_item("Site A", 1, self.now - timedelta(minutes=31))

        self.assertEqual(dashboard.topic_alerts(self.conn, now=self.now), [])

    def test_dashboard_escapes_headlines_and_explains_topic_matching(self):
        self.add_item("Site A", 1, self.now, title="<img src=x onerror=alert(1)>")

        html = dashboard.render(self.conn)

        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", html)
        self.assertNotIn("<img src=x", html)
        self.assertIn("não comprova que as fontes confirmaram o mesmo fato", html)
        self.assertIn('http-equiv="refresh" content="60"', html)

    def test_notification_count_severity_and_brasilia_times(self):
        self.add_item("Site A", 1, self.now - timedelta(minutes=2))
        self.add_item("Site B", 2, self.now - timedelta(minutes=1))
        self.add_item("Site C", 3, self.now)

        html = dashboard.render(self.conn, now=self.now)

        self.assertIn('aria-label="3 notícias recentes">3</span>', html)
        self.assertIn("ALERTA VERMELHO", html)
        self.assertIn("22/11/2026 09:00", html)
        self.assertIn("09:00", html)

    def test_four_severity_panels_include_recent_and_stale_news_sorted_by_publication(self):
        self.add_item("Site A", 1, self.now - timedelta(minutes=3))
        self.add_item("Site B", 2, self.now - timedelta(minutes=2))
        self.add_item("Site C", 3, self.now - timedelta(minutes=1))
        self.add_item("Site D", 4, self.now - timedelta(minutes=4), topic="business")
        self.add_item("Site E", 5, self.now - timedelta(minutes=2), topic="business")
        self.add_item("Site F", 6, self.now - timedelta(minutes=1), topic="monetary_policy")
        self.add_item("Old Site", 7, self.now - timedelta(minutes=31), topic="general")

        html = dashboard.render(self.conn, now=self.now)

        self.assertIn("VERMELHO", html)
        self.assertIn("AMARELO", html)
        self.assertIn("LARANJA", html)
        self.assertIn("VERDE", html)
        board = html.split('<div class="severity-board">', 1)[1]
        self.assertLess(board.index("Headline 3"), board.index("Headline 1"))
        self.assertIn("Headline 7", html)

    def test_static_dashboard_does_not_claim_to_auto_refresh(self):
        html = dashboard.render(self.conn, auto_refresh=False)

        self.assertNotIn('http-equiv="refresh"', html)
        self.assertIn("Arquivo estático", html)


if __name__ == "__main__":
    unittest.main()
