# Usage — News Intelligence Engine public V2

Use `python -m news_engine --help` for the command list. **All examples below are generic and standalone.**

## Offline

```
python -B -m news_engine demo --data-dir data
python -B -m news_engine stats --data-dir data
python -B -m unittest discover -s tests -v
```

## Feeds

1. Copy `examples/config.example.json` to `config.json`.
2. Replace the URL with a permitted public HTTPS source.
3. Run `python -B -m news_engine collect --config config.json --data-dir data`.

Supported `format` values are `rss`, `atom`, `xml` (auto-detect RSS/Atom), and `json` (flat list). JSON fields may be mapped by `list_key` and `fields` in the config. A response of 304 means no new material was downloaded.

## Queue-based ingestion

```
python -B -m news_engine enqueue-feeds --config config.json --batch-id example-batch --data-dir data
python -B -m news_engine work-once --config config.json --data-dir data
python -B -m news_engine queue-stats --data-dir data
```

Call `work-once` separately for each job. A lease that expires can be reclaimed; a failure is retried until the configured maximum, then moved to dead. A new batch ID enqueues the same feeds for a new pass. Nothing runs in the background by default.

## HTML and local API

```
python -B -m news_engine dashboard --data-dir data
python -B -m news_engine serve --data-dir data --host 127.0.0.1 --port 8080
```

`GET /api/items`, `GET /api/stats`, `GET /`; writes disallowed; only loopback bind.

## Gemini

Install `google-genai>=3.2.0` (see optional requirements), set `GEMINI_API_KEY` in your shell, and set `gemini.enabled: true` in config. Run `python -B -m news_engine review --config config.json --item-id 1 --data-dir data` to explicitly submit a stored item's title/summary for classification with the Decisions API. No review is automatic; the response is printed, not saved into the database.

## Privacy

Do not add real keys or restricted content to sample feeds, tests, Issues or Pull Requests. Publication timestamps and local ingestion times differ and should not be conflated.
