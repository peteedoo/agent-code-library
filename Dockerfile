# Agent Code Library — production API image
FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pyyaml

# Copy full repo (snippets, www/catalog.json, webhook, scripts, board)
COPY . /app

RUN chmod +x /app/scripts/entrypoint.sh \
  && python3 /app/scripts/indexer.py \
  && python3 /app/scripts/build_tarball.py || true

ENV PYTHONUNBUFFERED=1
ENV ACL_WEBHOOK_SECRET=""
ENV ACL_REBUILD_ON_START=0
ENV PORT=8000

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3)"

CMD ["/app/scripts/entrypoint.sh"]
