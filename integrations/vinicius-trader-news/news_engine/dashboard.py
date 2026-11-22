"""Self-contained local dashboard with recent topic coverage alerts."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit

from . import store
from .util import safe_text

ALERT_WINDOW = timedelta(minutes=30)
BRASILIA = ZoneInfo("America/Sao_Paulo")
NEWS_PER_PANEL = 10

STYLE = """
*{box-sizing:border-box}
:root{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:#142033;background:#f3f6fb}
body{margin:0;min-width:320px}
.topbar{background:linear-gradient(120deg,#101d32,#173955);color:#fff;padding:1.6rem max(1.25rem,calc((100vw - 1200px)/2))}
.topbar-inner{max-width:1200px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;gap:2rem}
.hero-copy{min-width:0}
.brand{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;color:#9ec5dd;font-weight:700}
h1{font-size:clamp(1.6rem,3vw,2.4rem);margin:.35rem 0}
.subtitle{margin:0;color:#d2dfeb}
.notification{min-width:116px;display:flex;flex-direction:column;align-items:center;gap:.25rem;text-align:center}
.notification-bell{position:relative;width:54px;height:48px;display:grid;place-items:center;color:#fff}
.notification-bell svg{width:32px;height:32px;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.notification-count{position:absolute;top:-2px;right:1px;min-width:22px;height:22px;padding:0 .32rem;border-radius:99px;background:#e8f1f8;color:#173955;display:grid;place-items:center;font-size:.74rem;font-weight:800}
.notification-status{font-size:.75rem;font-weight:850;letter-spacing:.035em}
.notification--red .notification-status{color:#ffb6b9}
.notification--yellow .notification-status{color:#ffe28a}
.notification--orange .notification-status{color:#ffc887}
.notification--none .notification-status{color:#d2dfeb}
.notification-detail{font-size:.7rem;color:#c4d2df}
main{max-width:1200px;margin:1.5rem auto;padding:0 1.25rem 3rem}
.section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:1.7rem 0 .8rem}
h2{font-size:1.15rem;margin:0}
.muted{color:#68778a;font-size:.88rem}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:.9rem}
.stat,.alert,.panel{background:#fff;border:1px solid #e1e8f0;border-radius:14px;box-shadow:0 5px 18px #172b4508}
.stat{padding:1rem 1.1rem}
.stat strong{font-size:1.7rem;display:block;color:#173955}
.stat span{color:#68778a;font-size:.86rem}
.alerts{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:1rem}
.alert{padding:1rem 1.1rem;border-left:5px solid #d78323}
.alert--yellow{border-left-color:#e5b323;background:#fffdf5}
.alert--red{border-left-color:#c63d47;background:#fff8f8}
.alert-head{display:flex;align-items:center;justify-content:space-between;gap:.8rem}
.alert h3{margin:.65rem 0 .25rem;font-size:1.08rem}
.badge{display:inline-flex;align-items:center;border-radius:99px;padding:.25rem .6rem;font-size:.75rem;font-weight:800;letter-spacing:.04em}
.badge--orange{background:#fff0dd;color:#9b4b00}
.badge--yellow{background:#fff2b8;color:#785b00}
.badge--red{background:#ffe0e1;color:#9b1c28}
.source-count{font-weight:700;color:#35465a;font-size:.86rem}
.source-list{list-style:none;padding:0;margin:.8rem 0 0;display:grid;gap:.65rem}
.source-list li{border-top:1px solid #e9edf2;padding-top:.6rem}
.source-meta{display:flex;justify-content:space-between;gap:.75rem;font-size:.78rem;color:#68778a}
.headline{font-size:.88rem;line-height:1.4;margin:.25rem 0 0;color:#26364b}
.hold{font-size:.84rem;font-weight:700;color:#9b1c28;margin:.75rem 0 0}
.notice,.panel{padding:1rem 1.1rem}
.notice{margin-top:1rem;background:#eef5fb;border:1px solid #d6e5f1;border-radius:12px;color:#42566e;font-size:.83rem;line-height:1.55}
.severity-board{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:.9rem}
.severity-panel{background:#fff;border:1px solid #e1e8f0;border-top:5px solid #46885d;border-radius:14px;overflow:hidden;min-width:0}
.severity-panel--red{border-top-color:#c63d47}
.severity-panel--yellow{border-top-color:#e5b323}
.severity-panel--orange{border-top-color:#d78323}
.severity-panel--green{border-top-color:#46885d}
.severity-heading{padding:.9rem .9rem .7rem;display:flex;justify-content:space-between;align-items:center;gap:.5rem}
.severity-heading h3{font-size:.9rem;margin:0}
.severity-heading span{font-size:.75rem;color:#68778a}
.severity-list{padding:0 .75rem .75rem;display:grid;gap:.65rem;max-height:520px;overflow-y:auto}
.news-card{border:1px solid #edf1f5;border-radius:10px;padding:.7rem}
.news-card h4{font-size:.84rem;line-height:1.4;margin:.4rem 0;color:#26364b}
.news-card-meta{display:flex;justify-content:space-between;gap:.5rem;font-size:.72rem;color:#68778a}
.news-card-time{font-size:.74rem;line-height:1.45;color:#35465a;margin:.35rem 0}
.severity-empty{padding:.7rem;color:#8290a1;font-size:.8rem}
.panel{overflow:hidden;padding:0}
.table-wrap{overflow-x:auto}
table{border-collapse:collapse;width:100%;font-size:.88rem}
th,td{border-bottom:1px solid #edf1f5;padding:.75rem .85rem;text-align:left;vertical-align:top}
th{background:#f8fafc;color:#5e6f84;font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;white-space:nowrap}
tr:last-child td{border-bottom:0}
a{color:#155d85;text-decoration:none}
a:hover{text-decoration:underline}
.empty{padding:1.5rem;color:#68778a;background:#fff;border:1px dashed #cbd6e2;border-radius:14px}
.footer{margin-top:1.2rem;color:#8290a1;font-size:.77rem}
@media(max-width:980px){.severity-board{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:600px){.topbar{padding:1.3rem 1rem}.topbar-inner{gap:.75rem}.notification{min-width:92px}.notification-bell{width:46px;height:42px}.notification-bell svg{width:29px;height:29px}main{padding:0 1rem 2rem}.section-head{align-items:start;flex-direction:column}.severity-board{grid-template-columns:1fr}}
"""


def _as_utc(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clock(value: datetime) -> str:
    return value.astimezone(BRASILIA).strftime("%H:%M %Z")


def _published_clock(value) -> str:
    parsed = _as_utc(value)
    if parsed is None:
        return "Horário não informado"
    return parsed.astimezone(BRASILIA).strftime("%d/%m/%Y %H:%M %Z")


def _item_time_label(item: dict) -> str:
    if item.get("published_at") and item.get("published_quality") != "future_suspect":
        return f"Publicado: {_published_clock(item['published_at'])}"
    observed = _published_clock(item.get("first_seen_at"))
    if item.get("published_quality") == "future_suspect":
        return f"Publicação suspeita; observado: {observed}"
    return f"Publicação não informada; observado: {observed}"


def topic_alerts(conn, *, now: datetime | None = None) -> list[dict]:
    """Summarize distinct feed names by configured topic in the last 30 minutes."""
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    since = now - ALERT_WINDOW
    rows = store.topic_observations(conn, since.isoformat(), now.isoformat())
    grouped: dict[str, dict[str, dict]] = defaultdict(dict)

    for row in rows:
        observed = _as_utc(row["observed_at"])
        if observed is None:
            continue
        topic = str(row["topic"])
        source = str(row["source"])
        source_info = grouped[topic].get(source)
        if source_info is None:
            grouped[topic][source] = {
                "source": source, "first_seen": observed, "last_seen": observed,
                "title": row["title"], "impact": row["impact"], "link": row["link"],
            }
            continue
        if observed < source_info["first_seen"]:
            source_info["first_seen"] = observed
        if observed >= source_info["last_seen"]:
            source_info.update({
                "last_seen": observed, "title": row["title"],
                "impact": row["impact"], "link": row["link"],
            })

    alerts = []
    for topic, sources in grouped.items():
        source_rows = sorted(sources.values(), key=lambda item: item["first_seen"])
        count = len(source_rows)
        if count >= 3:
            severity = "red"
            red_since = source_rows[2]["first_seen"]
            red_until = red_since + ALERT_WINDOW
        elif count == 2:
            severity, red_since, red_until = "yellow", None, None
        else:
            severity, red_since, red_until = "orange", None, None
        alerts.append({
            "topic": topic, "source_count": count, "severity": severity,
            "sources": sorted(source_rows, key=lambda item: item["source"].casefold()),
            "red_since": red_since, "red_until": red_until,
        })
    order = {"red": 0, "yellow": 1, "orange": 2}
    return sorted(alerts, key=lambda alert: (
        order[alert["severity"]], -alert["source_count"], alert["topic"].casefold()))


def _topic_label(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def _safe_link(value) -> str:
    text = str(value or "")
    try:
        parsed = urlsplit(text)
    except ValueError:
        return safe_text(text)
    if parsed.scheme.lower() not in ("http", "https") or not parsed.netloc:
        return safe_text(text)
    return f'<a href="{safe_text(text)}" target="_blank" rel="noopener noreferrer">Abrir notícia</a>'


def _alert_card(alert: dict) -> str:
    severity = alert["severity"]
    labels = {"red": "VERMELHO", "yellow": "AMARELO", "orange": "LARANJA"}
    descriptions = {
        "red": "3 ou mais fontes distintas têm notícias recentes neste tema.",
        "yellow": "2 fontes distintas têm notícias recentes neste tema.",
        "orange": "Apenas 1 fonte tem notícia recente neste tema; corroboração limitada.",
    }
    source_rows = "".join(
        f'<li><div class="source-meta"><strong>{safe_text(source["source"])}</strong>'
        f'<span>{_clock(source["last_seen"])}</span></div>'
        f'<p class="headline">{safe_text(source["title"])}</p>'
        f'<div class="source-meta"><span>Impacto classificado: {safe_text(source["impact"])}</span>'
        f'<span>{_safe_link(source["link"])}</span></div></li>'
        for source in alert["sources"])
    hold = ""
    if severity == "red" and alert["red_until"] is not None:
        hold = (f'<p class="hold">Aviso do usuário: aguardar 30 min antes de operar; '
                f'janela até {_clock(alert["red_until"])}.</p>')
    return (
        f'<article class="alert alert--{severity}">'
        f'<div class="alert-head"><span class="badge badge--{severity}">ALERTA {labels[severity]}</span>'
        f'<span class="source-count">{alert["source_count"]} '
        f'{"fonte" if alert["source_count"] == 1 else "fontes"}</span></div>'
        f'<h3>{safe_text(_topic_label(alert["topic"]))}</h3>'
        f'<p class="muted">{descriptions[severity]}</p>'
        f'<ul class="source-list">{source_rows}</ul>{hold}</article>'
    )


def _news_card(item: dict) -> str:
    return (
        f'<article class="news-card"><div class="news-card-meta">'
        f'<strong>{safe_text(item["source"])}</strong>'
        f'<span>{safe_text(_topic_label(item["topic"]))}</span></div>'
        f'<h4>{safe_text(item["title"])}</h4>'
        f'<p class="news-card-time">{safe_text(_item_time_label(item))}</p>'
        f'<div class="news-card-meta"><span>Impacto: {safe_text(item["impact"])}</span>'
        f'<span>{_safe_link(item["link"])}</span></div></article>'
    )


def _severity_panels(items: list[dict], alerts: list[dict], now: datetime) -> str:
    severity_by_topic = {alert["topic"]: alert["severity"] for alert in alerts}
    cutoff = now - ALERT_WINDOW
    grouped = {"red": [], "yellow": [], "orange": [], "green": []}
    for item in items:
        observed = _as_utc(item.get("first_seen_at"))
        severity = severity_by_topic.get(item["topic"]) if observed and observed > cutoff else None
        grouped[severity or "green"].append(item)

    labels = {
        "red": ("VERMELHO", "3 ou mais fontes no tema"),
        "yellow": ("AMARELO", "2 fontes no tema"),
        "orange": ("LARANJA", "1 fonte no tema"),
        "green": ("VERDE", "Sem alerta ativo na janela de 30 min"),
    }
    panels = []
    for severity in ("red", "yellow", "orange", "green"):
        label, description = labels[severity]
        news = grouped[severity]
        shown = news[:NEWS_PER_PANEL]
        cards = "".join(_news_card(item) for item in shown)
        if not cards:
            cards = '<div class="severity-empty">Nenhuma notícia neste nível.</div>'
        panels.append(
            f'<section class="severity-panel severity-panel--{severity}">'
            f'<div class="severity-heading"><h3>{label}</h3>'
            f'<span>{len(news)} notícia(s)</span></div>'
            f'<div class="severity-heading"><span>{description}</span>'
            f'<span>mais recentes primeiro</span></div>'
            f'<div class="severity-list">{cards}</div>'
            f'<div class="severity-empty">Exibindo {len(shown)} de {len(news)}.</div></section>'
        )
    return "".join(panels)


def render(conn, *, auto_refresh: bool = True, now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    now = now.astimezone(timezone.utc)
    items = store.dashboard_items(conn, 200)
    stats = store.stats(conn)
    alerts = topic_alerts(conn, now=now)
    recent_count = store.recent_news_count(
        conn, (now - ALERT_WINDOW).isoformat(), now.isoformat())
    primary = alerts[0] if alerts else None
    status = primary["severity"] if primary else "none"
    status_labels = {
        "red": "ALERTA VERMELHO",
        "yellow": "ALERTA AMARELO",
        "orange": "ALERTA LARANJA",
        "none": "SEM ALERTAS",
    }
    rows = "".join(
        f'<tr><td>{safe_text(_published_clock(i["published_at"]))}</td>'
        f'<td>{safe_text(i["source"])}</td><td>{_safe_link(i["link"])} '
        f'{safe_text(i["title"])}</td><td>{safe_text(_topic_label(i["topic"]))}</td>'
        f'<td>{safe_text(i["impact"])}</td><td>{safe_text(i["status"])}</td></tr>'
        for i in items)
    alert_html = "".join(_alert_card(alert) for alert in alerts)
    if not alert_html:
        alert_html = '<div class="empty">Nenhuma fonte publicou notícias dos temas configurados nos últimos 30 minutos.</div>'
    severity_panels = _severity_panels(items, alerts, now)
    source_count = store.distinct_source_count(conn)
    refresh_meta = '<meta http-equiv="refresh" content="60">' if auto_refresh else ""
    subtitle = ("Cobertura recente por tema e fonte, atualizada a cada minuto."
                if auto_refresh else
                "Arquivo estático: gere novamente o painel para atualizar os dados.")
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
{refresh_meta}<title>Painel de Notícias</title><style>{STYLE}</style></head>
<body>
<header class="topbar"><div class="topbar-inner"><div class="hero-copy"><div class="brand">News Intelligence Engine</div>
<h1>Painel de inteligência de notícias</h1>
<p class="subtitle">{subtitle}</p></div>
<aside class="notification notification--{status}" aria-label="Notificações recentes">
  <div class="notification-bell"><svg viewBox="0 0 24 24" aria-hidden="true">
    <path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/>
    <path d="M10 21h4"/></svg>
    <span class="notification-count" aria-label="{recent_count} notícias recentes">{recent_count}</span>
  </div>
  <strong class="notification-status">{status_labels[status]}</strong>
  <span class="notification-detail">{recent_count} notícias nos últimos 30 min</span>
</aside></div></header>
<main>
<section class="stats">
  <div class="stat"><strong>{stats['total']}</strong><span>Notícias armazenadas</span></div>
  <div class="stat"><strong>{stats['clusters']}</strong><span>Agrupamentos de conteúdo</span></div>
  <div class="stat"><strong>{source_count}</strong><span>Fontes registradas</span></div>
  <div class="stat"><strong>{len(alerts)}</strong><span>Temas com cobertura nos últimos 30 min</span></div>
</section>
<section>
  <div class="section-head"><div><h2>Alertas por tema</h2>
    <span class="muted">Fontes distintas observadas nos últimos 30 minutos</span></div>
    <span class="muted">Horário de Brasília</span></div>
  <div class="alerts">{alert_html}</div>
  <div class="notice"><strong>Como interpretar:</strong> 1 fonte = laranja; 2 = amarelo; 3 ou mais = vermelho.
  O agrupamento usa os temas configurados (por exemplo, notícias diferentes classificadas como economia podem
  aparecer no mesmo alerta); isso não comprova que as fontes confirmaram o mesmo fato.
  A fonte é o nome configurado no feed, então feeds do mesmo site com nomes diferentes contam separadamente.
  A pausa vermelha é um aviso informativo de 30 minutos, não é uma recomendação financeira e o sistema não executa operações.</div>
</section>
<section>
  <div class="section-head"><div><h2>Notícias por nível de alerta</h2>
    <span class="muted">Ordenadas pela publicação mais recente; horário de Brasília</span></div></div>
  <div class="severity-board">{severity_panels}</div>
</section>
<section>
  <div class="section-head"><div><h2>Notícias recentes</h2>
    <span class="muted">Até 200 itens ordenados pela data de publicação</span></div></div>
  <div class="panel table-wrap"><table><thead><tr><th>Publicação</th><th>Fonte</th><th>Notícia</th>
  <th>Tema</th><th>Impacto</th><th>Status</th></tr></thead>
  <tbody>{rows or '<tr><td colspan="6">Nenhuma notícia armazenada.</td></tr>'}</tbody></table></div>
</section>
<p class="footer">Dados locais · somente leitura · classificações por palavras-chave são heurísticas, não previsões. Horários exibidos em America/Sao_Paulo.</p>
</main>
</body></html>"""


def build(conn, path) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(conn, auto_refresh=False), encoding="utf-8")
    return p
