FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY . /app

RUN uv sync --frozen

ENV PYTHONPATH=/app/src

CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
