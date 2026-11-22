# Explicit, offline-only demonstration. No SDKs, secrets, or feeds are installed.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY news_engine/ /app/news_engine/

# Unprivileged account; all demo output goes to the ephemeral /tmp directory.
USER 65532:65532

ENTRYPOINT ["python", "-B", "-m", "news_engine"]
CMD ["demo", "--data-dir", "/tmp/news-data"]
