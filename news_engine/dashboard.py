"""Static, self-contained HTML dashboard (no external assets, no operational data)."""
from __future__ import annotations

from pathlib import Path

from . import store
from .util import safe_text

STYLE = """
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:2rem;color:#1b1b1b}
h1{margin:0 0 .25rem} .muted{color:#666} .cards{display:flex;gap:1rem;flex-wrap:wrap;margin:1rem 0}
.card{border:1px solid #ddd;border-radius:10px;padding:.75rem 1rem;min-width:120px}
table{border-collapse:collapse;width:100%;font-size:.92rem}
th,td{border-bottom:1px solid #eee;padding:.45rem;text-align:left;vertical-align:top}
th{background:#fafafa}
"""


def render(conn) -> str:
    items = store.list_items(conn, 200)
    stats = store.stats(conn)
    rows = "".join(
        f"<tr><td>{safe_text(i['published_at'])}</td><td>{safe_text(i['source'])}</td>"
        f"<td>{safe_text(i['title'])}</td><td>{safe_text(i['topic'])}</td>"
        f"<td>{safe_text(i['impact'])}</td><td>{safe_text(i['cluster_id'])}</td>"
        f"<td>{safe_text(i['status'])}</td></tr>" for i in items)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>News Intelligence Engine</title><style>{STYLE}</style></head>
<body>
<h1>News Intelligence Engine</h1>
<p class="muted">Generic local dashboard. Read-only. No operational data.</p>
<div class="cards">
  <div class="card"><strong>{stats['total']}</strong><div class="muted">items</div></div>
  <div class="card"><strong>{stats['clusters']}</strong><div class="muted">clusters</div></div>
</div>
<table><thead><tr><th>Published</th><th>Source</th><th>Title</th><th>Topic</th>
<th>Impact</th><th>Cluster</th><th>Status</th></tr></thead>
<tbody>{rows}</tbody></table>
</body></html>"""


def build(conn, path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(conn), encoding="utf-8")
    return p
