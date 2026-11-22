# Local dashboard and explicitly-invoked feed/AI commands.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements-optional.txt /app/requirements-optional.txt
RUN python -m pip install --no-cache-dir -r /app/requirements-optional.txt tzdata \
    && mkdir -p /data \
    && chown 65532:65532 /data
COPY news_engine/ /app/news_engine/

USER 65532:65532

ENTRYPOINT ["python", "-B", "-m", "news_engine"]
CMD ["serve", "--config", "/config/config.json", "--data-dir", "/data", \
     "--host", "0.0.0.0", "--allow-container-bind"]
