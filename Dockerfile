# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /app

# Устанавливаем зависимости
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Копируем исходный код
COPY src/ ./src/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src

# PYTHONPATH=/app/src позволяет uvicorn найти модули api, core и т.д.
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
