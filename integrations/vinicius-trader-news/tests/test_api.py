import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from news_engine import api, store


def rec():
    return {
        "content_hash": "api-hash", "cluster_id": "api-cluster", "source": "demo",
        "external_id": "1", "title": "API item", "summary": "Synthetic item.",
        "link": "https://example.org/api", "published_at": "2026-01-01T00:00:00+00:00",
        "first_seen_at": "2026-01-01T00:00:00+00:00", "topic": "science",
        "impact": "low", "confidence": 0.1, "status": "new", "simhash": 7,
    }


class ApiTests(unittest.TestCase):
    def test_local_read_only_api(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "news.db"
            conn = store.connect(db)
            store.init_db(conn)
            store.insert_item(conn, rec())
            conn.close()
            server = api.make_server(str(db), "127.0.0.1", 0)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                client = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
                client.request("GET", "/api/stats")
                response = client.getresponse()
                payload = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertEqual(payload["total"], 1)
                client.request("POST", "/api/stats")
                response = client.getresponse()
                self.assertEqual(response.status, 405)
                client.close()
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
