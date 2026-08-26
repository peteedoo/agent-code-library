FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir fastapi "uvicorn[standard]" pyyaml

COPY . /app
RUN chmod +x /app/scripts/entrypoint.sh \
  && python3 /app/scripts/indexer.py || true

ENV PYTHONUNBUFFERED=1
ENV ACL_WEBHOOK_SECRET=""
ENV ACL_REBUILD_ON_START=1
ENV PORT=8000

EXPOSE 8000
CMD ["/app/scripts/entrypoint.sh"]
