FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir fastapi uvicorn pydantic asyncpg aioredis slack-sdk requests

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "services.fastapi_app:app", "--host", "0.0.0.0", "--port", "8000"]
