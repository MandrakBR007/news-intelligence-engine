# Optional offline Docker demonstration — proposed V3 / Issue #15

This recipe runs **only the synthetic local demo**, with no network access
inside the container, no published ports, no worker loop, and no automatic
restart. It is a convenience for verifying the public code, **not** a
production deployment architecture.

## Build and run manually

```bash
docker build --tag news-intelligence-engine:offline-demo .
docker run --rm --network none --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m --security-opt no-new-privileges --cap-drop ALL news-intelligence-engine:offline-demo
```

Alternatively:

```bash
docker compose -f compose.offline.yml run --rm --build offline-demo
```

Both run the explicit CLI `demo` once with synthetic samples. SQLite and
dashboard outputs live in ephemeral `/tmp/news-data` and are discarded with
the container. No account information, persistent volumes, host directories
or API keys are included. The image copies **only** `news_engine/` into
`/app`; the build context also excludes common secret and local data files
through `.dockerignore`.

**Security caveats:** `python:3.11-slim` is currently a moving image tag.
Before a reproducible release, pin and maintain a verified digest and perform
an image vulnerability scan. `--network none` restricts container networking,
but the Docker engine still needs network access to pull base images during
build when the image is not cached. This container is intentionally not
suitable for network feed collection, public APIs or 24/7 operation.

The CI tests inspect the Docker/Compose configuration statically. They do
not build or execute Docker. No claim of runtime Docker validation is made.

## Review of *_v2 tests

The suffix does not indicate duplication. The currently reviewed tests
cover different expectations:

| Existing domain | Additional *_v2 coverage |
|---|---|
| `test_api.py`: synthetic local GET/POST | `test_api_v2.py`: remote-bind refusal |
| `test_sources.py`: RSS parsing | `test_sources_v2.py`: Atom, JSON, URL/DNS safety, redirects, cache |
| Queue: no older unsuffixed queue test | `test_queue_v2.py`: leases, retry/dead state, idempotency |
| Worker: no older unsuffixed worker test | `test_worker_v2.py`: enqueue and process synthetic feed |

All tests remain in place. Renaming may be considered later, but deleting
or merging modules based on their suffix would reduce coverage without a
verified test-by-test map.

## Português

O Docker é **opcional e somente demonstrativo**: executa o comando `demo`
uma vez, sem rede, sem portas publicadas e sem tarefas automáticas. Dados
sintéticos e saída em `/tmp` descartável. Os testes `_v2` complementam
os anteriores; não foram excluídos. Os checks automatizados inspecionam
a configuração, mas não executam o Docker. É necessária revisão de segurança
e validação real do build antes de anunciar suporte formal a contêineres.
