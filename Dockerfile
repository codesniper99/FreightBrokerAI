# Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/

RUN uv sync --locked

COPY src/ /app/src

COPY main.py /app/

EXPOSE 8000



CMD ["uv","run", "uvicorn", "src.webhook_api:app", "--host", "0.0.0.0", "--port", "${PORT:-8000}"]