# Dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock /app/

RUN uv sync --locked

COPY src/ /app/src
COPY db/ /app/db/
COPY main.py /app/
COPY frontend/dist /app/frontend/dist

EXPOSE 8000

# Use a literal port; no shell expansion in exec-form CMD
CMD ["uv", "run", "uvicorn", "src.webhook_api:app", "--host", "0.0.0.0", "--port", "8000"]