# 🚀 Подробная инструкция по деплою user-service

> **Цель:** задеплоить простой FastAPI-сервис без БД, Redis, RabbitMQ на VPS через GitHub Actions.  
> **Ошибка, которую решаем:** `Run mkdir -p ~/.ssh → Error: Process completed with exit code 1`

---

## 📋 Содержание

1. [Почему падает deploy — диагностика ошибки](#1-почему-падает-deploy--диагностика-ошибки)
2. [Ошибка build — denied: installation not allowed to Write organization package](#15-ошибка-на-этапе-build--denied-installation-not-allowed-to-write-organization-package)
3. [Как устроен процесс деплоя](#2-как-устроен-процесс-деплоя)
3. [Шаг 1 — Исправить Dockerfile](#3-шаг-1--исправить-dockerfile)
4. [Шаг 2 — Создать docker-compose.prod.yml](#4-шаг-2--создать-docker-composeprodyml)
5. [Шаг 3 — Создать GitHub Actions workflow](#5-шаг-3--создать-github-actions-workflow)
6. [Шаг 4 — Подготовить VPS](#6-шаг-4--подготовить-vps)
7. [Шаг 5 — Создать SSH-ключ для CI/CD](#7-шаг-5--создать-ssh-ключ-для-cicd)
8. [Шаг 6 — Настроить GitHub Secrets](#8-шаг-6--настроить-github-secrets)
9. [Шаг 7 — Создать .env.prod на сервере](#9-шаг-7--создать-envprod-на-сервере)
10. [Шаг 8 — Запустить деплой](#10-шаг-8--запустить-деплой)
11. [Проверка результата](#11-проверка-результата)
12. [Полезные команды для отладки](#12-полезные-команды-для-отладки)
13. [Чеклист перед каждым деплоем](#13-чеклист-перед-каждым-деплоем)

---

## 1. Почему падает deploy — диагностика ошибки

### Что значит ошибка

```
Run mkdir -p ~/.ssh
Error: Process completed with exit code 1.
```

**GitHub Actions выполняет шаги deploy-джобы сверху вниз.** Типичный шаг настройки SSH выглядит так:

```yaml
- name: Setup SSH key
  run: |
    mkdir -p ~/.ssh                                    # ← эта строка выводится в лог
    echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/id_rsa  # ← здесь ошибка
    chmod 600 ~/.ssh/id_rsa
    ssh-keyscan -H ${{ secrets.VPS_HOST }} >> ~/.ssh/known_hosts
```

Ошибка — **не в `mkdir -p ~/.ssh`** (эта команда не может упасть). Падает следующая строка блока `run`. GitHub Actions показывает имя ВСЕГО шага, а не конкретную строку.

### Три главные причины этой ошибки

| Причина | Признак | Решение |
|---------|---------|---------|
| **Secret `SSH_PRIVATE_KEY` пустой или не задан** | В Secrets на GitHub он отсутствует или пустой | Добавить ключ (раздел 7–8) |
| **Secret `VPS_HOST` пустой** | `ssh-keyscan` не может соединиться | Добавить IP сервера (раздел 8) |
| **Формат приватного ключа нарушен** | Ключ скопирован с лишними пробелами/переносами | Заново скопировать через `cat` |

> ⚡ **Самая частая причина:** секреты организации или репозитория не были добавлены в GitHub. Сначала полностью выполните раздел 7 и 8, затем снова запускайте деплой.

---

## 1.5 Ошибка на этапе build — denied: installation not allowed to Write organization package

### Что значит ошибка

```
denied: installation not allowed to Write organization package
ERROR: failed to build: denied: installation not allowed to Write organization package
```

Это ошибка **прав доступа** — встроенный `GITHUB_TOKEN` не имеет разрешения на запись пакетов в организацию.

### Причина

По умолчанию `GITHUB_TOKEN` имеет только права на чтение (`read`). Чтобы пушить Docker-образы в `ghcr.io`, джобе нужно явно указать `packages: write`.

### Два обязательных исправления

#### Исправление 1 — Добавить `permissions` в джобу `build` в `deploy.yml`

```yaml
  build:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: test

    # ← ДОБАВИТЬ ЭТИ СТРОКИ
    permissions:
      contents: read
      packages: write

    steps:
      ...
```

Без этого блока `GITHUB_TOKEN` работает только на чтение.

#### Исправление 2 — Настройка в GitHub организации

Даже с правильным `permissions` в workflow, организация должна разрешить Actions писать пакеты.

**Путь:** Организация (`KarpovOrg`) → **Settings** → **Actions** → **General**

Прокрутить вниз до раздела **"Workflow permissions"**:
- ✅ Выбрать **"Read and write permissions"**
- Нажать **Save**

> Если у вас нет доступа к настройкам организации — значит вы не Owner. Нужно зайти под аккаунтом владельца организации.

### После исправлений

Запустить деплой заново:
```powershell
git commit --allow-empty -m "fix: add packages:write permission to build job"
git push origin main
```

---

## 2. Как устроен процесс деплоя

Каждый `git push origin main` запускает 3 джобы в GitHub Actions:

```
git push origin main
      │
      ▼
┌─────────────┐    ┌─────────────┐    ┌──────────────────────────────┐
│    test      │───►│    build    │───►│           deploy             │
│             │    │             │    │                              │
│ pytest      │    │ docker build│    │ 1. SSH на VPS               │
│             │    │ docker push │    │ 2. cd /opt/.../user-service  │
│             │    │ → ghcr.io   │    │ 3. docker pull               │
└─────────────┘    └─────────────┘    │ 4. docker compose up -d      │
                                      └──────────────────────────────┘
```

**Для деплоя без БД/Redis/RabbitMQ** упрощаем до минимума:
- Запускается только **1 контейнер** — `user-service` (FastAPI приложение)
- Нет миграций, нет воркера TaskIQ
- Образ хранится в **ghcr.io** (GitHub Container Registry — бесплатно)
- Деплой = SSH на сервер + `docker pull` + `docker compose up -d`

---

## 3. Шаг 1 — Исправить Dockerfile

> ⚠️ Текущий `Dockerfile` использует `ubuntu:latest` и запускает `top` — это заглушка, не рабочий образ. Нужно заменить.

Откройте `Dockerfile` в корне репозитория и замените содержимое:

```dockerfile
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
```

> **Почему `src.main:app`?** Потому что код лежит в папке `src/`, а точка входа — `src/main.py`.

---

## 4. Шаг 2 — Создать docker-compose.prod.yml

> ⚠️ Файл `docker-compose.prod.yml` сейчас пустой. Заполните его.

Файл описывает, как запустить сервис на **продакшн сервере**.

```yaml
# docker-compose.prod.yml
services:
  user-service:
    image: ${IMAGE_NAME}:${IMAGE_TAG}
    container_name: user-service
    restart: unless-stopped
    env_file:
      - .env.prod                        # читает переменные из файла на сервере
    ports:
      - "8000:8000"                      # временно: прямой порт для проверки
    networks:
      - traefik-net
    labels:
      # Включаем Traefik
      - "traefik.enable=true"
      - "traefik.docker.network=traefik-net"
      # Роутинг: все запросы /api/v1/users → этот контейнер
      - "traefik.http.routers.user-service.rule=PathPrefix(`/api/v1`)"
      - "traefik.http.routers.user-service.entrypoints=websecure"
      - "traefik.http.routers.user-service.tls.certresolver=letsencrypt"
      - "traefik.http.services.user-service.loadbalancer.server.port=8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  traefik-net:
    external: true                       # сеть уже создана инфраструктурой
```

> **Примечание о портах:** строка `ports: - "8000:8000"` открывает порт напрямую — только для первоначальной проверки. После того как Traefik настроен, эту строку можно убрать.

---

## 5. Шаг 3 — Создать GitHub Actions workflow

Создайте файл `.github/workflows/deploy.yml` (создайте папки если их нет):

```
user-service/
└── .github/
    └── workflows/
        └── deploy.yml     ← создать этот файл
```

**Содержимое `deploy.yml`:**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  # Имя образа: ghcr.io/ВАШ_ORG/user-service
  IMAGE_NAME: ghcr.io/${{ github.repository_owner }}/user-service

jobs:
  # ─── 1. ТЕСТЫ ─────────────────────────────────────────────────────────────
  test:
    name: Run Tests
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        run: pip install -e ".[dev]"

      - name: Run tests
        env:
          USER_CONFIG__APP__APP_NAME: "user-service-test"
          USER_CONFIG__APP__DEBUG: "true"
        run: pytest src/tests/ -v

  # ─── 2. СБОРКА И ПУБЛИКАЦИЯ ОБРАЗА ────────────────────────────────────────
  build:
    name: Build & Push Docker Image
    runs-on: ubuntu-latest
    needs: test                          # запускается только если тесты прошли

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Log in to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}  # встроенный токен, ничего добавлять не нужно

      - name: Extract metadata (tags, labels)
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.IMAGE_NAME }}
          tags: |
            type=sha,prefix=sha-
            type=raw,value=latest

      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          file: ./Dockerfile
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # ─── 3. ДЕПЛОЙ НА СЕРВЕР ─────────────────────────────────────────────────
  deploy:
    name: Deploy to VPS
    runs-on: ubuntu-latest
    needs: build                         # запускается только если сборка прошла

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      # Настраиваем SSH-ключ для подключения к серверу
      - name: Setup SSH key
        run: |
          mkdir -p ~/.ssh
          echo "${{ secrets.SSH_PRIVATE_KEY }}" > ~/.ssh/deploy_key
          chmod 600 ~/.ssh/deploy_key
          ssh-keyscan -H "${{ secrets.VPS_HOST }}" >> ~/.ssh/known_hosts 2>/dev/null

      # Копируем docker-compose.prod.yml на сервер
      - name: Copy docker-compose to server
        run: |
          scp -i ~/.ssh/deploy_key \
            -o StrictHostKeyChecking=no \
            docker-compose.prod.yml \
            ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }}:${{ secrets.SERVICE_DIR }}/docker-compose.prod.yml

      # Подключаемся к серверу и запускаем сервис
      - name: Deploy service on VPS
        run: |
          ssh -i ~/.ssh/deploy_key \
            -o StrictHostKeyChecking=no \
            ${{ secrets.VPS_USER }}@${{ secrets.VPS_HOST }} << 'ENDSSH'
            set -e
            
            cd ${{ secrets.SERVICE_DIR }}
            
            # Логинимся в ghcr.io
            echo "${{ secrets.GHCR_TOKEN }}" | docker login ghcr.io \
              -u "${{ secrets.GHCR_USER }}" --password-stdin
            
            # Скачиваем новый образ
            IMAGE_NAME=${{ env.IMAGE_NAME }} \
            IMAGE_TAG=sha-$(echo ${{ github.sha }} | cut -c1-7) \
              docker compose -f docker-compose.prod.yml pull user-service
            
            # Перезапускаем контейнер (без простоя других сервисов)
            IMAGE_NAME=${{ env.IMAGE_NAME }} \
            IMAGE_TAG=sha-$(echo ${{ github.sha }} | cut -c1-7) \
              docker compose -f docker-compose.prod.yml up -d --no-deps user-service
            
            # Ждём старта контейнера
            sleep 5
            
            # Проверяем что контейнер запущен
            docker ps | grep user-service
            
            echo "✅ Деплой завершён успешно"
          ENDSSH
```

> **Важно:** `${{ github.repository_owner }}` автоматически подставляет имя организации или пользователя GitHub. Если репозиторий называется `KarpovOrg/user-service`, то `repository_owner = KarpovOrg`.

---

## 6. Шаг 4 — Подготовить VPS

Выполните в **веб-консоли TimeWeb** (или SSH).

### 6.1 Проверить, что Docker и сети уже есть

```bash
docker --version
docker network ls | grep -E "traefik-net|internal"
```

Если сетей нет — создать:
```bash
docker network create traefik-net
docker network create internal
```

### 6.2 Открыть нужные порты в UFW

```bash
ufw allow 8000    # порт user-service (временно, для проверки)
ufw status        # убедиться что 22, 80, 443 тоже открыты
```

### 6.3 Создать директорию для сервиса

```bash
mkdir -p /opt/microservices/user-service
```

---

## 7. Шаг 5 — Создать SSH-ключ для CI/CD

GitHub Actions нужен специальный SSH-ключ для подключения к серверу.

**Выполните в веб-консоли TimeWeb:**

```bash
# Генерируем ключ (нажмите Enter на оба вопроса — пароль НЕ нужен)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /root/.ssh/github_deploy

# Добавляем публичный ключ в список разрешённых
cat /root/.ssh/github_deploy.pub >> /root/.ssh/authorized_keys

# Выставляем правильные права
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

# ─── ВАЖНО: скопируйте весь вывод этой команды ───
cat /root/.ssh/github_deploy
```

Вывод будет выглядеть примерно так:
```
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACDМНОГО СИМВОЛОВ...
...
-----END OPENSSH PRIVATE KEY-----
```

**Скопируйте ВЕСЬ текст** от `-----BEGIN OPENSSH PRIVATE KEY-----` до `-----END OPENSSH PRIVATE KEY-----` включительно. Он понадобится в следующем шаге.

> ⚠️ **Ни в коем случае не добавляйте приватный ключ в репозиторий!** Только в GitHub Secrets.

---

## 8. Шаг 6 — Настроить GitHub Secrets

GitHub Secrets — это зашифрованные переменные, которые не видны в логах CI/CD.

### 8.1 Создать Personal Access Token для скачивания образов

Серверу нужен токен чтобы скачивать (`docker pull`) образы из ghcr.io.

1. Откройте GitHub → **Settings** (ваши личные настройки, не организации)  
   _(кнопка с аватаром → Settings)_
2. В левом меню: **Developer settings** (самый низ)
3. **Personal access tokens** → **Tokens (classic)**
4. **Generate new token (classic)**
5. Заполните:
   - **Note:** `ghcr-read-packages`
   - **Expiration:** No expiration (или 1 год)
   - **Scopes:** ✅ `read:packages`
6. Нажмите **Generate token**
7. **Скопируйте токен сразу** — он показывается только один раз!

### 8.2 Добавить секреты в организацию (один раз для всех сервисов)

**Путь:** Организация → **Settings** → **Secrets and variables** → **Actions** → **New organization secret**

> При добавлении каждого секрета выбирайте **Policy: All repositories**

| Название секрета | Значение | Где взять |
|-----------------|----------|-----------|
| `SSH_PRIVATE_KEY` | Весь текст из `cat /root/.ssh/github_deploy` | Раздел 7 выше |
| `VPS_HOST` | IP-адрес вашего VPS | Панель TimeWeb |
| `VPS_USER` | `root` | |
| `GHCR_TOKEN` | Personal Access Token из шага 8.1 | |
| `GHCR_USER` | Ваш логин GitHub (личный, не org) | |

#### Как правильно скопировать SSH_PRIVATE_KEY

Ошибки чаще всего из-за неправильного копирования ключа. Соблюдайте:
- Копируйте **весь текст**, включая строки `-----BEGIN...` и `-----END...`
- **Не добавляйте** лишних пробелов или переносов
- Вставляйте в поле Value как есть — GitHub сохранит как многострочный секрет

Проверить, что ключ скопирован верно (в веб-консоли сервера):
```bash
# Должны показать одинаковый fingerprint
ssh-keygen -lf /root/.ssh/github_deploy       # приватный
ssh-keygen -lf /root/.ssh/github_deploy.pub   # публичный
```

### 8.3 Добавить секрет SERVICE_DIR в репозиторий

Этот секрет уникален для каждого сервиса.

**Путь:** Репозиторий → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Название секрета | Значение |
|-----------------|----------|
| `SERVICE_DIR` | `/opt/microservices/user-service` |

### 8.4 Проверить наличие всех секретов

После добавления у вас должны быть:

**На уровне организации:**
- ✅ `SSH_PRIVATE_KEY`
- ✅ `VPS_HOST`
- ✅ `VPS_USER`
- ✅ `GHCR_TOKEN`
- ✅ `GHCR_USER`

**На уровне репозитория:**
- ✅ `SERVICE_DIR`

**Встроенные (добавлять не нужно):**
- ✅ `GITHUB_TOKEN` — автоматически предоставляется GitHub Actions

---

## 9. Шаг 7 — Создать .env.prod на сервере

В **веб-консоли TimeWeb** создайте файл с переменными окружения для продакшна:

```bash
nano /opt/microservices/user-service/.env.prod
```

Содержимое для простого сервиса **без БД/Redis/RabbitMQ**:

```env
# Имя сервиса
USER_CONFIG__APP__APP_NAME=user-service
USER_CONFIG__APP__DEBUG=false
```

Сохранить: `Ctrl+O` → `Enter` → `Ctrl+X`

Проверить что файл создался:
```bash
cat /opt/microservices/user-service/.env.prod
```

> **Формат переменных** следует конфигурации из `src/core/config.py`:
> - `USER_CONFIG__` — это `env_prefix`
> - `APP__APP_NAME` — это путь через вложенные модели (`app.app_name`)

---

## 10. Шаг 8 — Запустить деплой

### 10.1 Зафиксировать все изменения

В PowerShell (на вашем компьютере):

```powershell
cd C:\Users\Stefan\Desktop\KarpovOrg\user-service

# Добавляем все изменённые/созданные файлы
git add Dockerfile
git add docker-compose.prod.yml
git add .github/workflows/deploy.yml

# Коммит
git commit -m "fix: add proper Dockerfile, docker-compose.prod.yml and deploy workflow"

# Пуш в main — это запустит CI/CD
git push origin main
```

### 10.2 Следить за прогрессом

1. Откройте ваш репозиторий на GitHub
2. Перейдите на вкладку **Actions** (верхнее меню)
3. Кликните на самый последний запуск (вверху списка)
4. Увидите 3 джобы: `test` → `build` → `deploy`
5. Кликните на `deploy` → разверните шаги для подробностей

### 10.3 Что должно происходить в каждой джобе

**Джоба `test`:**
```
✅ Checkout code
✅ Set up Python 3.13
✅ Install dependencies
✅ Run tests
```

**Джоба `build`:**
```
✅ Checkout code
✅ Log in to GitHub Container Registry
✅ Extract metadata
✅ Build and push Docker image   ← занимает 1-3 минуты
```

**Джоба `deploy`:**
```
✅ Checkout code
✅ Setup SSH key
✅ Copy docker-compose to server
✅ Deploy service on VPS
```

---

## 11. Проверка результата

### 11.1 На сервере (веб-консоль TimeWeb)

```bash
# Проверяем что контейнер запущен
docker ps | grep user-service

# Ожидаемый вывод:
# CONTAINER ID   IMAGE                              STATUS         PORTS
# abc123def456   ghcr.io/karpovorg/user-service:sha-XXXXXXX   Up 2 minutes   0.0.0.0:8000->8000/tcp
```

```bash
# Проверяем health check напрямую
curl http://localhost:8000/api/v1/health/

# Ожидаемый ответ:
# {"service":"auth-service","status":"ok"}
```

```bash
# Смотрим логи контейнера
docker logs user-service --tail=30
```

### 11.2 Через браузер

Если Traefik настроен и DNS указывает на сервер:
```
https://karpov1.duckdns.org/api/v1/health/
```

Если хотите проверить напрямую по IP (пока Traefik не настроен):
```
http://ВАШ_VPS_IP:8000/api/v1/health/
```

### 11.3 Если что-то не работает

```bash
# Посмотреть все контейнеры (включая упавшие)
docker ps -a | grep user-service

# Посмотреть подробные логи (последние 50 строк)
docker logs user-service --tail=50

# Зайти внутрь контейнера для отладки
docker exec -it user-service /bin/bash

# Проверить переменные окружения внутри контейнера
docker exec user-service env | grep USER_CONFIG
```

---

## 12. Полезные команды для отладки

### Если деплой упал — смотрим логи GitHub Actions

В GitHub → Actions → нажать на упавший run → кликнуть на джобу `deploy` → развернуть упавший шаг.

### Проверить SSH-соединение вручную

В веб-консоли сервера:
```bash
# Проверяем что authorized_keys содержит ключ
cat /root/.ssh/authorized_keys

# Должна быть строка: ssh-ed25519 AAAA... github-actions-deploy
```

Если хотите проверить ключ с Windows (PowerShell):
```powershell
# Создайте временный файл с ключом и попробуйте подключиться
# (только для диагностики, не для постоянного использования)
```

### Пересоздать SSH-ключ если что-то пошло не так

В веб-консоли сервера:
```bash
# Удаляем старый ключ
rm /root/.ssh/github_deploy /root/.ssh/github_deploy.pub

# Создаём новый
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /root/.ssh/github_deploy

# Добавляем публичный ключ
cat /root/.ssh/github_deploy.pub >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh && chmod 600 /root/.ssh/authorized_keys

# Выводим приватный ключ — СКОПИРОВАТЬ В GitHub Secret SSH_PRIVATE_KEY
cat /root/.ssh/github_deploy
```

После этого **обновите секрет `SSH_PRIVATE_KEY`** в GitHub (организация → Settings → Secrets → SSH_PRIVATE_KEY → Update).

### Обновить сервис вручную (без CI/CD)

Если нужно срочно обновить сервис, не дожидаясь CI/CD:

```bash
cd /opt/microservices/user-service

# Логин в реестр
echo "ВАШ_GHCR_TOKEN" | docker login ghcr.io -u ВАШ_GITHUB_USERNAME --password-stdin

# Скачать последний образ
IMAGE_NAME=ghcr.io/karpovorg/user-service IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml pull user-service

# Перезапустить
IMAGE_NAME=ghcr.io/karpovorg/user-service IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml up -d --no-deps user-service
```

---

## 13. Чеклист перед каждым деплоем

### Файлы в репозитории ✅

- [ ] `Dockerfile` — рабочий, запускает `uvicorn src.main:app`
- [ ] `docker-compose.prod.yml` — не пустой, содержит сервис `user-service`
- [ ] `.github/workflows/deploy.yml` — создан по шаблону из раздела 5

### GitHub Secrets ✅

- [ ] **Организация:** `SSH_PRIVATE_KEY` добавлен (весь текст ключа)
- [ ] **Организация:** `VPS_HOST` = IP адрес VPS
- [ ] **Организация:** `VPS_USER` = `root`
- [ ] **Организация:** `GHCR_TOKEN` = Personal Access Token (read:packages)
- [ ] **Организация:** `GHCR_USER` = ваш логин GitHub
- [ ] **Репозиторий:** `SERVICE_DIR` = `/opt/microservices/user-service`

### На сервере ✅

- [ ] Директория `/opt/microservices/user-service/` создана
- [ ] Файл `/opt/microservices/user-service/.env.prod` создан
- [ ] Docker-сеть `traefik-net` существует (`docker network ls`)
- [ ] Публичный ключ добавлен в `~/.ssh/authorized_keys`
- [ ] Порт 8000 открыт в UFW (`ufw allow 8000`)

### После деплоя ✅

- [ ] Все 3 джобы в GitHub Actions зелёные ✅
- [ ] `docker ps | grep user-service` — контейнер запущен
- [ ] `curl http://localhost:8000/api/v1/health/` — возвращает `{"status": "ok"}`
- [ ] Логи без ошибок: `docker logs user-service --tail=20`

---

## 💡 Как это работает дальше

После первого успешного деплоя процесс становится автоматическим:

1. Вы пишете код → `git push origin main`
2. GitHub Actions автоматически:
   - Запускает тесты
   - Собирает Docker-образ
   - Пушит в ghcr.io
   - Деплоит на сервер
3. Через 3–5 минут новый код уже работает на сервере

**Добавление нового сервиса** — повторяете те же шаги для нового репозитория. Org-секреты (`SSH_PRIVATE_KEY`, `VPS_HOST`, `VPS_USER`, `GHCR_TOKEN`, `GHCR_USER`) добавляются **один раз** и наследуются всеми репозиториями организации. Для нового сервиса добавляете только `SERVICE_DIR`.

---

## 🗄️ Подключение PostgreSQL (users_schema + users)

> Выполняйте команды через **веб-консоль TimeWeb** или SSH.

### Что произошло в коде

| Файл | Что добавлено |
|------|--------------|
| `src/migrations/env.py` | Async Alembic env — читает `settings.db.url` |
| `src/migrations/versions/0001_create_users.py` | Создаёт схему `users_schema` и таблицу `users` |
| `alembic.ini` | `script_location = src/migrations` |
| `docker-compose.prod.yml` | Сервис `migrate` + сеть `internal` |
| `.github/workflows/deploy.yml` | Шаг `docker compose run --rm migrate` перед рестартом |

---

### Шаг 1 — Обновить `.env.prod` на сервере

```bash
nano /opt/microservices/user-service/.env.prod
```

Добавьте эти строки (пароль уже ваш из инфраструктуры):

```env
USER_CONFIG__APP__APP_NAME=user-service
USER_CONFIG__APP__DEBUG=false

# PostgreSQL — hostname "postgres" — это имя контейнера в сети internal
USER_CONFIG__DB__URL=postgresql+asyncpg://postgres:faUtUONuz5SJBlAQmXSH@postgres:5432/mydb
USER_CONFIG__DB__ECHO=false
```

Сохранить: `Ctrl+O` → `Enter` → `Ctrl+X`

> ⚠️ Hostname `postgres` — именно так называется контейнер PostgreSQL в сети `internal`.  
> Порт `5432`. База — `mydb` (ваша существующая база из инфраструктуры).

---

### Шаг 2 — Запустить деплой

Просто запушьте код в `main` — CI/CD сделает всё автоматически:

```powershell
git add .
git commit -m "Add database: users_schema migration"
git push origin main
```

**Что произойдёт в GitHub Actions:**
```
✅ test    → pytest (SQLite in-memory, без реального PostgreSQL)
✅ build   → docker build + push в ghcr.io
✅ deploy  →
           1. docker compose pull user-service      (скачивает новый образ)
           2. docker compose run --rm migrate       (запускает миграции)
              → CREATE SCHEMA users_schema
              → CREATE TABLE users_schema.users
              → CREATE INDEX ix_users_id
              → CREATE INDEX ix_users_uid
           3. docker compose up -d user-service     (перезапускает приложение)
```

---

### Шаг 3 — Проверить на сервере

После успешного деплоя:

```bash
# 1. Проверить что таблица создалась
docker exec -it postgres psql -U postgres -d mydb -c "\dn"
# Должна появиться: users_schema

docker exec -it postgres psql -U postgres -d mydb -c "\dt users_schema.*"
# Должна появиться: users_schema | users | table

# 2. Проверить логи миграций
docker logs user-service-migrate 2>&1 | tail -20
# Ожидаемый вывод:
# INFO  [alembic.runtime.migration] Running upgrade  -> 0001, create users_schema and users table

# 3. Проверить логи приложения
docker logs user-service --tail=20
# Ожидаемый вывод:
# ✅ Подключение к БД установлено

# 4. Проверить health-check
curl http://localhost:8000/api/v1/health/
# {"service":"user-service","status":"ok"}
```

---

### Если нужно запустить миграции вручную (без пуша)

Если вы уже задеплоили образ и просто хотите применить миграции:

```bash
cd /opt/microservices/user-service

# Применить все миграции
IMAGE_NAME=ghcr.io/karpovorg/user-service \
IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml run --rm migrate

# Посмотреть текущее состояние миграций
IMAGE_NAME=ghcr.io/karpovorg/user-service \
IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml run --rm migrate \
  python -m alembic current

# Откатить последнюю миграцию
IMAGE_NAME=ghcr.io/karpovorg/user-service \
IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml run --rm migrate \
  python -m alembic downgrade -1
```

---

### Как добавить следующую миграцию

Когда нужно изменить схему БД (добавить колонку, таблицу и т.д.):

**1. Создайте файл миграции** в `src/migrations/versions/`:

```
src/migrations/versions/0002_add_email_to_users.py
```

```python
revision: str = "0002"
down_revision: str = "0001"   # ← ссылка на предыдущую миграцию

def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email", sa.String(255), nullable=True),
        schema="users_schema",
    )

def downgrade() -> None:
    op.drop_column("users", "email", schema="users_schema")
```

**2. Пушьте** — CI/CD автоматически применит новую миграцию.

> 💡 **Правило цепочки:** каждая миграция ссылается на предыдущую через `down_revision`.  
> Alembic применяет их строго по порядку: `0001` → `0002` → `0003` → ...

---

### Структура файлов Alembic

```
user-service/
├── alembic.ini                          ← конфигурация (script_location = src/migrations)
└── src/
    └── migrations/
        ├── __init__.py
        ├── env.py                       ← async engine, читает settings.db.url
        ├── script.py.mako               ← шаблон для новых миграций
        └── versions/
            └── 0001_create_users.py     ← CREATE SCHEMA users_schema + CREATE TABLE users
```

---

## 📡 Тестирование User endpoints

После успешного деплоя сервис поднят на `http://<VPS_IP>:8000`.  
Если у вас настроен Traefik — через `https://your-domain.com`.

### Через Swagger UI (браузер)

Откройте в браузере:
```
http://<VPS_IP>:8000/docs
```
Или через домен (если настроен Traefik + TLS):
```
https://your-domain.com/docs
```

Там будут доступны два endpoint:
- `POST /api/v1/users/create` — создать пользователя
- `GET  /api/v1/users/all`    — получить всех пользователей

---

### Через curl на сервере

```bash
# ─── Создать пользователя ───────────────────────────────────────
curl -s -X POST http://localhost:8000/api/v1/users/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Ivan", "surname": "Petrov"}' | python3 -m json.tool

# Ожидаемый ответ:
# {
#   "message": "Пользователь успешно создан",
#   "name": "Ivan",
#   "surname": "Petrov"
# }

# ─── Получить всех пользователей ────────────────────────────────
curl -s http://localhost:8000/api/v1/users/all | python3 -m json.tool

# Ожидаемый ответ:
# [
#   {
#     "name": "Ivan",
#     "surname": "Petrov",
#     "id": 1,
#     "uid": "550e8400-e29b-41d4-a716-446655440000",
#     "created_at": "2026-04-14T10:30:00+00:00"
#   }
# ]
```

---

### Через curl с вашего компьютера

```powershell
# ─── Создать пользователя ───────────────────────────────────────
$body = '{"name": "Ivan", "surname": "Petrov"}'
Invoke-RestMethod -Method POST `
  -Uri "http://<VPS_IP>:8000/api/v1/users/create" `
  -ContentType "application/json" `
  -Body $body

# ─── Получить всех пользователей ────────────────────────────────
Invoke-RestMethod -Method GET `
  -Uri "http://<VPS_IP>:8000/api/v1/users/all"
```

---

### Прямая проверка данных в БД

```bash
# Зайти в psql и посмотреть записи
docker exec -it postgres psql -U postgres -d mydb \
  -c "SELECT id, uid, name, surname, created_at FROM users_schema.users;"

# Или в одну строку
docker exec -it postgres psql -U postgres -d mydb -c "SELECT * FROM users_schema.users LIMIT 10;"
```

---

### Если endpoint возвращает ошибку 500

```bash
# 1. Посмотреть логи сервиса
docker logs user-service --tail=50

# 2. Проверить подключение к БД из контейнера
docker exec -it user-service python3 -c "
import asyncio
from core.database import db_client
asyncio.run(db_client.dispose())
print('DB connection OK')
"

# 3. Убедиться что .env.prod содержит правильный URL
cat /opt/microservices/user-service/.env.prod | grep DB_URL
# Должно быть: USER_CONFIG__DB__URL=postgresql+asyncpg://postgres:<password>@postgres:5432/mydb

# 4. Убедиться что user-service и postgres в одной сети
docker inspect user-service | python3 -m json.tool | grep -A 20 '"Networks"'
# Должна быть сеть "internal"
```

---

### Типичные ошибки при работе с endpoints

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `Connection refused` | Контейнер не запущен или порт не прокинут | `docker ps` → проверить порт `8000:8000` |
| `could not connect to server` | Нет сети `internal` или контейнер postgres не запущен | Проверить `docker network inspect internal` |
| `relation "users_schema.users" does not exist` | Миграции не применились | Запустить `docker compose run --rm migrate` вручную |
| `column ... does not exist` | Новая миграция не применилась | Перезапустить CI/CD пайплайн |

