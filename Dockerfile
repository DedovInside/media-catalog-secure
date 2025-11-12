# syntax=docker/dockerfile:1.7-labs

# Этап сборки — установка зависимостей и компиляция
FROM python:3.11-slim AS build
WORKDIR /build

# Устанавливаем системные зависимости, необходимые для сборки
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt requirements-dev.txt ./

# Создаём wheel-файлы
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip wheel --wheel-dir=/wheels -r requirements.txt && \
    pip wheel --wheel-dir=/wheels -r requirements-dev.txt

# Этап выполнения — продакшен
FROM python:3.11-slim AS runtime

# Безопасность: создаём непривилегированного пользователя
RUN groupadd -r -g 1000 appuser && \
    useradd -r -u 1000 -g appuser -d /app -s /bin/bash appuser

# Устанавливаем только необходимые системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Настраиваем рабочую директорию приложения
WORKDIR /app

# Устанавливаем из requirements.txt, используя wheel файлы
COPY --from=build /wheels /tmp/wheels
COPY requirements.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install --no-cache-dir --find-links /tmp/wheels -r requirements.txt && \
    rm -rf /tmp/wheels

# Копируем исходный код приложения
COPY --chown=appuser:appuser . .

# Безопасность: переключаемся на непривилегированного пользователя
USER appuser

# Переменные окружения для продакшена
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app" \
    ENV=production

# Проверка состояния (healthcheck) для FastAPI
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Открываем порт 8000
EXPOSE 8000

# Команда запуска приложения в продакшене
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

# Этап выполнения — тесты
FROM runtime AS test

# Устанавливаем dev-зависимости для тестов
USER root
COPY --from=build /wheels /tmp/wheels
COPY requirements-dev.txt ./
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir --find-links /tmp/wheels -r requirements-dev.txt && \
    rm -rf /tmp/wheels && \
    mkdir -p /app/.pytest_cache && \
    chown appuser:appuser /app/.pytest_cache
USER appuser

# Переменные окружения для тестов
ENV ENV=test
