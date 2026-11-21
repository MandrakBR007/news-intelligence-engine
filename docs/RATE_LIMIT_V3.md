# Optional feed cooldown and queue diagnostics (Issue #13)

Status: proposed V3 functionality, initially off by default. No always-on worker.

Configure `queue.min_feed_interval_seconds` with an integer from 0 to 86400.
The default **0** keeps the existing manual feed behavior. For example:

```json
{"queue": {"min_feed_interval_seconds": 60}}
```

A nonzero value enforces a minimum gap between the **starts** of successive attempts for the same exact configured feed URL across manual job batches. The tool does not sleep or schedule work: `work-once` returns `deferred` when a job is put back in the queue until its allowed time. Deferral does not consume an attempt. Use `queue-stats` to inspect `ready`, `delayed`, and `expired_leases` counts without exposing feed URLs. All data stays in local SQLite; the throttle table stores only SHA-256 feed keys and next-allowed times.

**Limitations:** This is a local per-feed start cooldown, not a globally distributed API quota manager or a guarantee against all network bursts. Feed URL variants are distinct keys. Validation of allowed HTTPS destinations remains in the existing fetcher. Reserving time before a failed request still enforces the cooldown. There is no automatic refresh, worker loop, external timer or background process.

Deterministic offline tests cover adjacent batches, different feeds, disabled default, invalid configuration, numerical diagnostics and elapsed leases.

## Português

O intervalo opcional por feed limita o início das tentativas de coleta manual. `0` mantém o comportamento antigo. Um trabalho pode retornar `deferred` e permanecer pendente até o próximo horário, sem perder tentativas. O diagnóstico da fila retorna somente contagens numéricas, sem URLs. Não há execução automática, agendamento contínuo nem nova integração externa.
