# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Устанавливаем системные зависимости (curl нужен для healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Устанавливаем зависимости
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Копируем исходный код (включает src/migrations/)
COPY src/ ./src/

# alembic.ini должен лежать в WORKDIR (/app), чтобы `python -m alembic` нашёл его
COPY alembic.ini ./

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# PYTHONPATH=/app/src позволяет uvicorn найти модули api, core и т.д.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
