FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir fastapi uvicorn[standard] pyyaml

COPY . /app

ENV PYTHONUNBUFFERED=1
ENV ACL_WEBHOOK_SECRET=""

EXPOSE 8000

CMD ["uvicorn", "webhook.main:app", "--host", "0.0.0.0", "--port", "8000"]
