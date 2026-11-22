"""Loopback-only read-only HTTP UI. Deliberately unauthenticated and local."""
from __future__ import annotations

import ipaddress
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import cli_output, dashboard, health, store


def make_server(db_path, host: str = "127.0.0.1", port: int = 8080) -> ThreadingHTTPServer:
    try:
        addr = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("bind must be an explicit loopback IP") from exc
    if host != "127.0.0.1":
        raise ValueError("only 127.0.0.1 is supported; use a separate authenticated proxy")

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: str, content_type: str = "text/plain; charset=utf-8"):
            data = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):  # noqa: N802
            # Reject attacker-controlled Host headers (including DNS rebinding).
            if self.headers.get("Host", "").split(":", 1)[0].lower() not in ("127.0.0.1", "localhost"):
                self._send(403, "invalid host")
                return
            if self.path not in ("/", "/api/stats", "/api/items", "/api/health"):
                self._send(404, "not found")
                return
            conn = store.connect(db_path)
            store.init_db(conn)
            try:
                if self.path == "/api/stats":
                    self._send(200, json.dumps(store.stats(conn), ensure_ascii=False),
                               "application/json; charset=utf-8")
                elif self.path == "/api/health":
                    snapshot = cli_output.public_result("health", health.diagnostic_snapshot(conn))
                    self._send(200, json.dumps(snapshot, ensure_ascii=False),
                               "application/json; charset=utf-8")
                elif self.path == "/api/items":
                    self._send(200, json.dumps(store.list_items(conn, limit=100), ensure_ascii=False),
                               "application/json; charset=utf-8")
                else:
                    self._send(200, dashboard.render(conn), "text/html; charset=utf-8")
            finally:
                conn.close()

        def do_POST(self):  # noqa: N802
            self._send(405, "read-only")

        def log_message(self, *args):
            return

    return ThreadingHTTPServer((host, int(port)), Handler)


def serve(db_path, host: str = "127.0.0.1", port: int = 8080) -> None:
    server = make_server(db_path, host, port)
    print(f"Local read-only interface: http://{host}:{server.server_address[1]}/")
    server.serve_forever()
