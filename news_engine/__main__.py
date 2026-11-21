"""Explicit CLI. No task scheduling, trading or background auto-start."""
from __future__ import annotations

import argparse
import json

from . import api, cli_output, config as config_mod, dashboard, demo, gemini_client, pipeline, queue, store, worker


def _open(config, data_dir):
    db = config_mod.db_path(config, data_dir)
    conn = store.connect(db)
    store.init_db(conn)
    return conn, db


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="news_engine", description="Public news feed research toolkit")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("demo", "collect", "dashboard", "stats", "serve", "enqueue-feeds", "work-once", "queue-stats", "review"):
        p = sub.add_parser(cmd)
        p.add_argument("--data-dir", default="data")
        p.add_argument("--config", default=None, required=cmd in ("collect", "enqueue-feeds", "work-once", "review"))
        if cmd == "serve":
            p.add_argument("--host", default=None)
            p.add_argument("--port", type=int, default=None)
        if cmd == "review":
            p.add_argument("--item-id", type=int, required=True)
        if cmd == "enqueue-feeds":
            p.add_argument("--batch-id", default=None)
    args = parser.parse_args(argv)
    if args.command == "demo":
        print(json.dumps(cli_output.public_result(args.command, demo.run(args.data_dir, args.config)), ensure_ascii=False, indent=2))
        return 0
    config = config_mod.load_config(args.config)
    if args.command == "collect":
        result = pipeline.run(config, args.data_dir)
        conn, _ = _open(config, args.data_dir)
        result["dashboard"] = str(dashboard.build(conn, config_mod.dashboard_path(config, args.data_dir)))
        conn.close()
        print(json.dumps(cli_output.public_result(args.command, result), ensure_ascii=False, indent=2))
        return 0

    conn, db = _open(config, args.data_dir)
    try:
        if args.command == "dashboard":
            output = {"dashboard": str(dashboard.build(conn, config_mod.dashboard_path(config, args.data_dir)))}
        elif args.command == "stats":
            output = store.stats(conn)
        elif args.command == "enqueue-feeds":
            output = {"added": worker.enqueue_feeds(conn, config, batch_id=args.batch_id), "queue": queue.stats(conn)}
        elif args.command == "work-once":
            output = worker.work_once(conn, config)
        elif args.command == "queue-stats":
            output = queue.diagnostics(conn)
        elif args.command == "review":
            if not config["gemini"].get("enabled"):
                output = {"enabled": False, "reason": "set gemini.enabled=true to opt in"}
            else:
                item = store.get_item(conn, args.item_id)
                if item is None:
                    parser.error("item ID not found")
                output = gemini_client.review(item["title"], item["summary"],
                    model=config["gemini"].get("model", "gemini-decision-1"),
                    key_env=config["gemini"].get("api_key_env", "GEMINI_API_KEY"))
        elif args.command == "serve":
            conn.close()
            api.serve(str(db), args.host or config["http"].get("host", "127.0.0.1"),
                      args.port if args.port is not None else config["http"].get("port", 8080))
            return 0
        else:
            parser.error("unrecognized command")
        print(json.dumps(cli_output.public_result(args.command, output), ensure_ascii=False, indent=2))
        return 0
    finally:
        if args.command != "serve":
            conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
