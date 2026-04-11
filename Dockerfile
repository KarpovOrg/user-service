# syntax=docker/dockerfile:1
FROM python:3.13-slim AS base

# Системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Устанавливаем зависимости через pip
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"

# Копируем исходный код
COPY src/ ./src/

# Пользователь без root-прав (безопасность)
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# Порт приложения
EXPOSE 8000

# Переменные окружения по умолчанию
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Запуск
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]