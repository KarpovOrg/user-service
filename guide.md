# 🚀 FastAPI Микросервисы на TimeWeb VPS — без Kubernetes

> **Стек:** FastAPI · PostgreSQL · Redis · RabbitMQ · TaskIQ · Docker Compose · Traefik · Portainer · GitHub Actions  
> **Подход:** Один VPS, Docker Compose, автоматический SSL, управление через браузер

---

## 📋 Содержание

1. [Архитектура](#1-архитектура)
2. [Создание VPS на TimeWeb](#2-создание-vps-на-timeweb)
3. [Веб-консоль TimeWeb — главный инструмент](#3-веб-консоль-timeweb--главный-инструмент)
4. [SSH из Windows PowerShell (опционально)](#4-ssh-из-windows-powershell-опционально)
5. [Начальная настройка сервера](#5-начальная-настройка-сервера)
6. [Настройка DNS](#6-настройка-dns)
7. [Запуск инфраструктуры](#7-запуск-инфраструктуры)
8. [Portainer — управление Docker через браузер](#8-portainer--управление-docker-через-браузер)
9. [Шаблон микросервиса — как использовать](#9-шаблон-микросервиса--как-использовать)
10. [Создание организации и репозитория на GitHub](#10-создание-организации-и-репозитория-на-github)
11. [SSH-ключ для GitHub Actions](#11-ssh-ключ-для-github-actions)
12. [Секреты GitHub Actions](#12-секреты-github-actions)
13. [Подготовка VPS к первому деплою](#13-подготовка-vps-к-первому-деплою)
14. [Первый деплой](#14-первый-деплой)
15. [Добавление второго и последующих микросервисов](#15-добавление-второго-и-последующих-микросервисов)
16. [Межсервисное взаимодействие](#16-межсервисное-взаимодействие)
17. [Полезные команды](#17-полезные-команды)
18. [Чеклист](#18-чеклист)

> 🔐 **Аутентификация (JWT + сессии + Traefik ForwardAuth):** смотрите [`auth.md`](auth.md)

---

## 1. Архитектура

### Что получится в итоге

```
Интернет
    │
    ▼
[TimeWeb VPS — Ubuntu 22.04]
    │
    ├── Traefik (порты 80/443)        ← reverse proxy, автоматический SSL
    │       │
    │       ├──► my-service (FastAPI)  ← ваш микросервис 1
    │       ├──► order-service         ← ваш микросервис 2
    │       └──► karpov1.duckdns.org/api/v1/... ← единая точка входа для всех сервисов
    │
    ├── Portainer   → http://karpov1.duckdns.org:9000   ← веб-управление Docker
    ├── RabbitMQ UI → http://karpov1.duckdns.org:15672  ← мониторинг очередей
    │
    ├── my-service-worker (TaskIQ)     ← обрабатывает фоновые задачи
    ├── PostgreSQL                     ← общая БД (разные БД на сервис)
    ├── Redis                          ← кеш + result backend TaskIQ
    └── RabbitMQ                       ← брокер сообщений между сервисами
```

### Docker-сети

| Сеть | Назначение |
|------|-----------|
| `traefik-net` | Traefik видит контейнеры, роутит HTTP/HTTPS трафик |
| `internal` | Микросервисы ↔ PostgreSQL / Redis / RabbitMQ (без доступа снаружи) |

### Почему не Kubernetes

- Один VPS от **~600–900 руб/месяц** против K8s кластера от **~5000–8000 руб/месяц**
- Docker Compose достаточно для небольшого проекта
- Меньше конфигурации, проще отлаживать
- Portainer даёт красивый веб-интерфейс вместо `kubectl`

---

## 2. Создание VPS на TimeWeb

### Шаги

1. Зайдите на [timeweb.cloud](https://timeweb.cloud) и авторизуйтесь
2. В меню слева: **Облачные серверы** → **Создать сервер**
3. Выберите параметры:

| Параметр | Рекомендация |
|----------|-------------|
| **ОС** | Ubuntu 22.04 LTS |
| **CPU** | 2 vCPU |
| **RAM** | 4 GB (минимум для старта) |
| **Диск** | 50 GB SSD |
| **Цена** | ~700–900 руб/месяц |

4. Придумайте **root-пароль** (запишите его!)
5. Нажмите **Создать сервер**
6. Дождитесь создания (1–3 минуты) — сервер появится в списке с **IP-адресом**

> 💡 **IP-адрес** вашего VPS — запишите его, он понадобится везде

---

## 3. Веб-консоль TimeWeb — главный инструмент

Вам не нужен SSH-клиент на своём компьютере. TimeWeb предоставляет **браузерный терминал**.

### Как открыть

1. В панели TimeWeb: **Облачные серверы** → нажмите на ваш сервер
2. Перейдите на вкладку **Консоль** (или кнопка "Открыть консоль")
3. Откроется браузерное окно терминала
4. Введите логин: `root`, затем пароль (который указали при создании)

### Советы по работе в веб-консоли

- **Копирование команд:** вставьте через **Ctrl+Shift+V** или правую кнопку мыши
- **Если застряло:** нажмите **Enter** — иногда терминал просто ждёт
- **Очистить экран:** команда `clear`
- Веб-консоль работает даже если SSH не настроен — это ваш запасной вариант всегда

---

## 4. SSH из Windows PowerShell (опционально)

> Если вам удобнее работать в веб-консоли TimeWeb — этот раздел можно **пропустить**. SSH потребуется только для настройки CI/CD (GitHub Actions выполняет это автоматически).

В Windows 10/11 OpenSSH встроен — установка не нужна.

### Генерация SSH-ключа (в PowerShell)

```powershell
# Генерируем ключ (нажмите Enter на все вопросы)
ssh-keygen -t ed25519 -C "my-vps-key"

# Ключи создаются в:
# C:\Users\ВашеИмя\.ssh\id_ed25519       (приватный — никому не давать!)
# C:\Users\ВашеИмя\.ssh\id_ed25519.pub   (публичный — можно передавать)
```

### Копирование ключа на сервер

```powershell
# Скопировать публичный ключ на сервер (замените YOUR_VPS_IP)
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh root@YOUR_VPS_IP "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

### Подключение

```powershell
# Подключиться к серверу
ssh root@YOUR_VPS_IP

# Если SSH работает — увидите приглашение: root@server:~#
```

### Если SSH не работает

1. Убедитесь что порт 22 открыт в UFW (шаг 5)
2. Проверьте правильность IP
3. **Используйте веб-консоль** — это всегда работает

---

## 5. Начальная настройка сервера

> Выполните эти команды в **веб-консоли TimeWeb**. Вставляйте блоками.

### Обновление системы

```bash
apt update && apt upgrade -y
```

### Установка базовых утилиты

```bash
apt install -y curl git htop nano ufw apache2-utils
```

### Установка Docker

```bash
# Официальный скрипт установки Docker
curl -fsSL https://get.docker.com | bash

# Проверяем
docker --version
docker compose version
```

Ожидаемый вывод:
```
Docker version 26.x.x, build ...
Docker Compose version v2.x.x
```

### Настройка файрвола (UFW)

```bash
# Разрешаем нужные порты
ufw allow 22      # SSH
ufw allow 80      # HTTP (Traefik перенаправит на HTTPS)
ufw allow 443     # HTTPS

# Включаем файрвол
ufw enable
# Введите: y

# Проверяем
ufw status
```

### Создание рабочих директорий

```bash
mkdir -p /opt/microservices/infra
mkdir -p /opt/microservices/letsencrypt

# Создаём файл для хранения SSL сертификатов
touch /opt/microservices/infra/letsencrypt/acme.json
chmod 600 /opt/microservices/infra/letsencrypt/acme.json
```

---

## 6. Настройка DNS

✅ **Домен уже зарегистрирован:** `karpov1.duckdns.org`

Осталось **указать IP вашего VPS** в DuckDNS:

1. Зайдите на [duckdns.org](https://www.duckdns.org) и войдите в аккаунт
2. Найдите домен `karpov1` → в поле **current ip** введите IP вашего VPS
3. Нажмите **update ip**
4. Готово — через 1–2 минуты `karpov1.duckdns.org` будет указывать на ваш сервер

### Адреса всех сервисов

> ⚠️ **Важно:** DuckDNS не поддерживает сабдомены (`portainer.karpov1.duckdns.org` работать не будет). Поэтому Portainer и RabbitMQ открываем через прямые порты — это удобнее и проще.

| Сервис | Адрес | Протокол |
|--------|-------|---------|
| **API микросервисов** | `https://karpov1.duckdns.org/api/v1/...` | HTTPS (Let's Encrypt) |
| **Portainer** | `http://karpov1.duckdns.org:9000` | HTTP, прямой порт |
| **RabbitMQ UI** | `http://karpov1.duckdns.org:15672` | HTTP, прямой порт |
| **Traefik Dashboard** | `http://karpov1.duckdns.org:8080` | HTTP, прямой порт |

### Открываем порты в UFW (добавляем к уже настроенным 22/80/443)

```bash
ufw allow 8080    # Traefik Dashboard
ufw allow 9000    # Portainer
ufw allow 15672   # RabbitMQ Management UI
ufw status        # проверяем
```

---

## 7. Запуск инфраструктуры

> Домен `karpov1.duckdns.org` уже настроен и указывает на ваш VPS ✅  
> Используем конфигурацию **с SSL** (Let's Encrypt автоматически выдаст сертификат).

### Копируем файлы инфраструктуры на сервер

Выполните в **веб-консоли** (создаём файлы напрямую):

```bash
cd /opt/microservices/infra
```

#### Создаём traefik.yml

```bash
cat > traefik.yml << 'EOF'
log:
  level: INFO

entryPoints:
  web:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: websecure
          scheme: https
          permanent: true
  websecure:
    address: ":443"

certificatesResolvers:
  letsencrypt:
    acme:
      email: YOUR_EMAIL@example.com
      storage: /letsencrypt/acme.json
      httpChallenge:
        entryPoint: web

api:
  dashboard: true
  insecure: false

providers:
  docker:
    exposedByDefault: false
    network: traefik-net
EOF
```

> ⚠️ **Замените `YOUR_EMAIL@example.com`** на ваш настоящий email — Let's Encrypt его использует

#### Генерируем надёжные пароли

```bash
# Генерируем случайные пароли
POSTGRES_PASS=$(openssl rand -base64 20 | tr -dc 'a-zA-Z0-9' | head -c 20)
REDIS_PASS=$(openssl rand -base64 20 | tr -dc 'a-zA-Z0-9' | head -c 20)
RABBIT_PASS=$(openssl rand -base64 20 | tr -dc 'a-zA-Z0-9' | head -c 20)
TRAEFIK_PASS_HASH=$(htpasswd -nb admin $(openssl rand -base64 12) | sed 's/\$/\$\$/g')

echo "=== СОХРАНИТЕ ЭТИ ДАННЫЕ ==="
echo "POSTGRES_PASSWORD=$POSTGRES_PASS"
echo "REDIS_PASSWORD=$REDIS_PASS"
echo "RABBITMQ_PASSWORD=$RABBIT_PASS"
echo "TRAEFIK_AUTH=$TRAEFIK_PASS_HASH"
```

**Скопируйте вывод и сохраните в надёжное место!**

#### Создаём .env

```bash
cat > .env << 'EOF'
DOMAIN=karpov1.duckdns.org

POSTGRES_DB=mydb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ВСТАВЬТЕ_POSTGRES_PASS

REDIS_PASSWORD=ВСТАВЬТЕ_REDIS_PASS

RABBITMQ_USER=admin
RABBITMQ_PASSWORD=ВСТАВЬТЕ_RABBIT_PASS
EOF
```

> Пароли — из вывода команды выше. Редактировать: `nano .env`

#### Создаём docker-compose.yml

Скопируйте содержимое файла `templates/infra/docker-compose.yml` из этого репозитория:

```bash
# Вариант 1: если репозиторий уже клонирован на сервере
# cp /path/to/repo/templates/infra/docker-compose.yml .

# Вариант 2: создать вручную через nano
nano docker-compose.yml
# (вставьте содержимое файла templates/infra/docker-compose.yml)
```

### Создаём Docker сети

```bash
docker network create traefik-net
docker network create internal
```

### Запускаем инфраструктуру

```bash
cd /opt/microservices/infra
docker compose up -d
```

### Проверяем что всё запустилось

```bash
docker compose ps
```

Ожидаемый вывод (все сервисы `healthy` или `running`):
```
NAME         STATUS
traefik      running
postgres     healthy
redis        healthy
rabbitmq     healthy
portainer    running
```

Если сервис не запустился — смотрим логи:
```bash
docker compose logs postgres     # логи postgres
docker compose logs rabbitmq     # логи rabbitmq
docker compose logs -f traefik   # логи traefik в реальном времени
```

### Проверяем Traefik Dashboard

Откройте в браузере: `http://karpov1.duckdns.org:8080/dashboard/`  
(Dashboard открыт без пароля — он доступен только если вы знаете порт 8080)

> Если страница не открывается — проверьте что порт 8080 открыт в UFW: `ufw allow 8080`

---

## 8. Portainer — управление Docker через браузер

После запуска инфраструктуры Portainer доступен по адресу:

**`http://karpov1.duckdns.org:9000`**

### Первый вход

1. Откройте `http://karpov1.duckdns.org:9000` в браузере
2. **Создайте учётную запись администратора** (придумайте пароль, минимум 12 символов)
3. На главном экране: выберите **"local"** среду (Local Docker environment)
4. Нажмите **Connect**

### Что умеет Portainer (без SSH!)

| Действие | Где в Portainer |
|---------|-----------------|
| Просмотр всех контейнеров | Containers |
| Логи контейнера | Containers → контейнер → Logs |
| **Терминал внутри контейнера** | Containers → контейнер → Console → Connect |
| Restart/Stop контейнера | Containers → кнопки действий |
| Просмотр volumes | Volumes |
| Просмотр сетей | Networks |
| Просмотр образов | Images |

> 💡 **Portainer Console** — это замена SSH. Вы можете зайти в любой контейнер прямо из браузера и выполнять команды.

---

## 9. Шаблон микросервиса — как использовать

Папка `templates/microservice-template/` — готовый шаблон, который нужно **скопировать и переименовать** для каждого нового сервиса.

### Структура шаблона

```
microservice-template/
├── src/
│   ├── main.py                        # точка входа FastAPI
│   ├── core/
│   │   ├── config.py                  # настройки через pydantic-settings
│   │   ├── lifespan.py                # startup/shutdown (broker, logging)
│   │   ├── database/
│   │   │   ├── base.py                # DeclarativeBase
│   │   │   └── db_client.py           # async engine + get_db dependency
│   │   ├── exceptions/__init__.py     # кастомные исключения
│   │   ├── logging/logger.py          # setup_logging, get_logger
│   │   ├── rabbitmq/
│   │   │   ├── base.py                # абстрактный RabbitMQ клиент
│   │   │   └── rabbitmq_client.py     # прямая публикация через aio_pika
│   │   ├── redis/
│   │   │   ├── base.py                # абстрактный Redis клиент
│   │   │   └── redis_client.py        # redis_client синглтон + get_redis
│   │   └── taskiq/
│   │       ├── base.py                # абстрактный BrokerBase
│   │       └── taskiq_client.py       # broker (AioPikaBroker + Redis backend)
│   ├── api/
│   │   ├── api_v1/
│   │   │   ├── __init__.py            # агрегатор роутеров v1
│   │   │   └── items.py               # CRUD эндпоинты (пример)
│   │   ├── depends/__init__.py        # общие FastAPI зависимости
│   │   └── middlewares/__init__.py    # CORS и прочие middleware
│   ├── models/
│   │   ├── base.py                    # re-export Base
│   │   ├── item.py                    # пример модели (замените/добавьте)
│   │   └── mixins/__init__.py         # UUIDPrimaryKeyMixin, TimestampMixin
│   ├── repositories/
│   │   └── base.py                    # Generic BaseRepository (CRUD)
│   ├── schemas/__init__.py            # Pydantic схемы (ItemCreate/Update/Response)
│   ├── services/
│   │   └── item_service.py            # бизнес-логика
│   ├── messaging/
│   │   ├── consumers/__init__.py      # TaskIQ задачи (обработчики)
│   │   └── publishers/__init__.py     # публикация событий другим сервисам
│   └── tests/
│       ├── conftest.py                # тестовое окружение (SQLite, моки)
│       └── test_items.py              # тесты CRUD эндпоинтов
├── alembic/env.py                     # async Alembic миграции
├── alembic/versions/                  # файлы миграций
├── Dockerfile                         # многоэтапная сборка
├── docker-compose.yml                 # локальная разработка (+ infra)
├── docker-compose.prod.yml            # продакшн деплой (с SSL)
├── docker-compose.prod.no-ssl.yml     # продакшн деплой (без SSL)
├── .github/workflows/deploy.yml       # GitHub Actions CI/CD
├── pyproject.toml                     # зависимости
└── .env.example                       # пример переменных окружения
```

### Что нужно заменить при создании нового сервиса

1. **Имя сервиса** — замените `my-service` на ваше имя везде:
   - `docker-compose.prod.yml`: имена сервисов `my-service`, `my-service-worker`
   - `pyproject.toml`: `name = "my-service"`
   - `src/core/config.py`: `APP_NAME = "my-service"`

2. **Путь Traefik** в `docker-compose.prod.yml`:
   ```yaml
   - "traefik.http.routers.my-service.rule=PathPrefix(`/api/v1/items`)"
   # Замените /api/v1/items на путь вашего сервиса
   # Например: /api/v1/users, /api/v1/orders, /api/v1/products
   ```

3. **Модели** — создайте свои в `src/models/`, наследуйтесь от `Base` + миксины:
   ```python
   from src.models.base import Base
   from src.models.mixins import UUIDPrimaryKeyMixin, TimestampMixin

   class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
       __tablename__ = "orders"
       ...
   ```
   Импортируйте модель в `alembic/env.py` чтобы автогенерация миграций её видела.

4. **Роутеры** — добавляйте в `src/api/api_v1/`, регистрируйте в `src/api/api_v1/__init__.py`

5. **Задачи** — TaskIQ задачи пишите в `src/messaging/consumers/__init__.py`

6. **Переменные .env** — замените на реальные значения для продакшна

### Локальная разработка

```bash
# Клонировали репозиторий, перешли в папку
cp .env.example .env          # создаём локальный .env
docker compose up -d          # запускаем всё (приложение + infra)
docker compose exec app alembic upgrade head   # применяем миграции

# Создание новой миграции после изменения модели
docker compose exec app alembic revision --autogenerate -m "add users table"
docker compose exec app alembic upgrade head

# Тесты (без Docker, нужен Python локально)
pip install -e ".[dev]"
pytest src/tests/ -v

# Просмотр логов
docker compose logs -f app
docker compose logs -f worker
```

---

## 10. Создание организации и репозитория на GitHub

### Создаём организацию

1. Зайдите на [github.com](https://github.com) и авторизуйтесь
2. Нажмите **+** (вверху справа) → **New organization**
3. Выберите план **Free** → введите имя организации (например `karpov-services`)
4. Нажмите **Create organization**

### Создаём репозиторий для сервиса

1. На странице организации: **Repositories** → **New repository**
2. Owner: **karpov-services** (ваша организация)
3. Name: `my-service` (или `user-service`, `order-service` и т.д.)
4. Visibility: **Private**
5. Нажмите **Create repository**

### GitHub Container Registry (ghcr.io)

GitHub предоставляет **бесплатный Container Registry** для каждого репозитория.  
Адрес образа: `ghcr.io/karpov-services/my-service`

Настраивается **автоматически** — дополнительных действий не нужно.  
Сборка CI/CD использует встроенный `GITHUB_TOKEN` для push в реестр.

### Загружаем шаблон в репозиторий

```powershell
# Копируем шаблон
Copy-Item -Recurse "C:\путь\к\templates\microservice-template" "C:\projects\my-service"
cd "C:\projects\my-service"

# Удаляем устаревшие папки и файлы (остались от предыдущей версии шаблона)
Remove-Item -Recurse -Force "app", "tests", ".gitlab-ci.yml" -ErrorAction SilentlyContinue

# Инициализируем git и пушим
git init -b main
git remote add origin https://github.com/karpov-services/my-service.git
git add .
git commit -m "Initial commit from template"
git push -u origin main
```

---

## 11. SSH-ключ для GitHub Actions

GitHub Actions нужен SSH-доступ к серверу для деплоя. Создаём специальную ключевую пару.

### Генерируем ключ (в веб-консоли TimeWeb)

```bash
# Создаём ключ специально для CI/CD (без passphrase — Enter на оба вопроса)
ssh-keygen -t ed25519 -C "github-actions-deploy" -f /root/.ssh/github_deploy

# Добавляем публичный ключ в authorized_keys
cat /root/.ssh/github_deploy.pub >> /root/.ssh/authorized_keys
chmod 700 /root/.ssh
chmod 600 /root/.ssh/authorized_keys

# Выводим ПРИВАТНЫЙ ключ — скопируем его в GitHub Secrets
cat /root/.ssh/github_deploy
```

Скопируйте весь вывод — начиная с `-----BEGIN OPENSSH PRIVATE KEY-----` и до `-----END OPENSSH PRIVATE KEY-----` включительно.

---

## 12. Секреты GitHub Actions

В GitHub Secrets хранятся все конфиденциальные переменные для деплоя.

### Создаём Personal Access Token для GHCR

Серверу нужен токен чтобы скачивать (`pull`) образы из ghcr.io.

1. GitHub → **Settings** (личные, не организации) → **Developer settings**
2. **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
3. Note: `ghcr-read-packages`
4. Expiration: **No expiration** (или 1 год)
5. Scopes: поставьте галочку **`read:packages`**
6. Нажмите **Generate token** → **скопируйте токен** (показывается один раз!)

### Добавляем секреты на уровне организации

Секреты организации автоматически доступны во **всех** репозиториях — добавляем один раз.

**Организация → Settings → Secrets and variables → Actions → New organization secret**

| Secret | Значение | Примечание |
|--------|----------|-----------|
| `SSH_PRIVATE_KEY` | Содержимое `/root/.ssh/github_deploy` (весь текст) | Ключ из раздела 11 |
| `VPS_HOST` | IP-адрес вашего VPS | Например `185.123.45.67` |
| `VPS_USER` | `root` | |
| `GHCR_TOKEN` | Personal Access Token из шага выше | read:packages |
| `GHCR_USER` | Ваш GitHub логин (не org, а личный) | Например `karpov` |

При добавлении секрета — поставьте **Policy: All repositories**.

### Добавляем SECRET уровня репозитория

`SERVICE_DIR` уникален для каждого сервиса — добавляем в каждый репозиторий отдельно.

**Репозиторий → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значение |
|--------|----------|
| `SERVICE_DIR` | `/opt/microservices/my-service` |

### Встроенные переменные GitHub (добавлять не нужно)

| Переменная | Значение |
|-----------|---------|
| `secrets.GITHUB_TOKEN` | Автоматический токен для push в ghcr.io при сборке |
| `github.sha` | SHA текущего коммита |
| `github.repository` | `karpov-services/my-service` |
| `github.actor` | Имя пользователя, запустившего workflow |

---

## 13. Подготовка VPS к первому деплою

### Создаём директорию для сервиса

В **веб-консоли TimeWeb**:

```bash
mkdir -p /opt/microservices/my-service
```

### Создаём .env.prod

```bash
nano /opt/microservices/my-service/.env.prod
```

Содержимое (замените пароли на реальные из раздела 7):

```env
APP_NAME=my-service
DEBUG=false
SECRET_KEY=сгенерируйте-длинный-случайный-ключ

# PostgreSQL — пароль из .env инфраструктуры
DATABASE_URL=postgresql+asyncpg://postgres:ВАШ_POSTGRES_PASS@postgres:5432/mydb

# RabbitMQ — пароль из .env инфраструктуры
RABBITMQ_URL=amqp://admin:ВАШ_RABBIT_PASS@rabbitmq:5672/

# Redis — пароль из .env инфраструктуры
REDIS_URL=redis://:ВАШ_REDIS_PASS@redis:6379/0
```

Сохранить: `Ctrl+O` → `Enter` → `Ctrl+X`

### Генерируем SECRET_KEY

```bash
# Генерируем случайный ключ
openssl rand -hex 32
# Скопируйте вывод в .env.prod вместо "сгенерируйте-длинный-случайный-ключ"
```

### Создаём отдельную базу данных для сервиса

```bash
# Заходим в PostgreSQL (замените ВАШ_POSTGRES_PASS)
docker exec -it postgres psql -U postgres -c "CREATE DATABASE mydb;"

# Для второго сервиса:
docker exec -it postgres psql -U postgres -c "CREATE DATABASE orders_db;"
docker exec -it postgres psql -U postgres -c "CREATE DATABASE users_db;"
```

> 💡 Каждый сервис использует **отдельную базу данных**, но один PostgreSQL инстанс

### Логинимся в GitHub Container Registry на сервере

Один раз вводим команду на сервере, чтобы Docker запомнил учётные данные для `ghcr.io`:

```bash
# Замените YOUR_GITHUB_USERNAME и YOUR_GHCR_TOKEN на реальные значения
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GHCR_TOKEN
# Сохранится в /root/.docker/config.json — при CI/CD токен обновляется автоматически
```

> Этот шаг необязателен — CI/CD логинится автоматически при каждом деплое.

---

## 14. Первый деплой

### Настраиваем workflow для вашего сервиса

В файле `.github/workflows/deploy.yml` убедитесь что имена сервисов в `docker-compose.prod.yml` совпадают:

```yaml
# docker-compose.prod.yml — имена сервисов для деплоя
services:
  my-service:        # ← должно совпадать со строкой в deploy.yml
  my-service-worker: # ← должно совпадать со строкой в deploy.yml
  migrate:           # ← для миграций
```

В `.github/workflows/deploy.yml` в шаге `Деплоим` строки:
```yaml
docker compose -f docker-compose.prod.yml pull my-service my-service-worker
docker compose -f docker-compose.prod.yml up -d --no-deps my-service my-service-worker
```

### Пушим код и запускаем пайплайн

```powershell
# Делаем коммит и пушим в main
git add .
git commit -m "Deploy my-service"
git push origin main
```

### Следим за пайплайном

1. Откройте репозиторий на GitHub
2. Перейдите на вкладку **Actions**
3. Кликните на текущий workflow run — видны все шаги

```
✅ test    → pytest запускает тесты
✅ build   → docker build + push в ghcr.io
✅ deploy  → SSH на сервер → pull → migrate → restart
```

### Проверяем что сервис запустился

В **веб-консоли TimeWeb**:

```bash
docker ps | grep my-service
# Должны быть: my-service и my-service-worker в статусе Up

# Проверяем health check
curl http://localhost:8000/healthz
# {"status": "ok", "service": "my-service"}
```

В браузере откройте:
```
https://karpov1.duckdns.org/api/v1/items
```

### Проверяем логи деплоя

```bash
docker logs my-service --tail=50
docker logs my-service-worker --tail=50
```

Или через **Portainer** → Containers → my-service → Logs

---

## 15. Добавление второго и последующих микросервисов

Каждый новый сервис — это **повтор тех же шагов**. Процесс становится быстрее.

### Чеклист для нового сервиса

#### 1. Создаём новый репозиторий на GitHub

Организация `karpov-services` → **New repository** → Название: `order-service`

#### 2. Копируем шаблон, переименовываем

```powershell
Copy-Item -Recurse "templates\microservice-template" "C:\projects\order-service"
cd "C:\projects\order-service"

# Удаляем устаревшие папки и файлы
Remove-Item -Recurse -Force "app", "tests", ".gitlab-ci.yml" -ErrorAction SilentlyContinue
```

Находим и заменяем `my-service` → `order-service` в файлах:
- `docker-compose.prod.yml` — имена сервисов
- `pyproject.toml` — `name = "order-service"`
- `src/core/config.py` — `APP_NAME = "order-service"`

Меняем PathPrefix в `docker-compose.prod.yml`:
```yaml
- "traefik.http.routers.order-service.rule=PathPrefix(`/api/v1/orders`)"
```

#### 3. Добавляем секрет уровня репозитория на GitHub

**Репозиторий → Settings → Secrets and variables → Actions → New repository secret**

| Secret | Значение |
|--------|----------|
| `SERVICE_DIR` | `/opt/microservices/order-service` |

> Остальные секреты (`SSH_PRIVATE_KEY`, `VPS_HOST`, `VPS_USER`, `GHCR_TOKEN`, `GHCR_USER`) уже добавлены на уровне **организации** — они наследуются автоматически

#### 4. Создаём директорию и .env.prod на сервере

```bash
mkdir -p /opt/microservices/order-service
nano /opt/microservices/order-service/.env.prod
```

```env
APP_NAME=order-service
DEBUG=false
SECRET_KEY=другой-ключ-для-этого-сервиса

DATABASE_URL=postgresql+asyncpg://postgres:PASS@postgres:5432/orders_db
RABBITMQ_URL=amqp://admin:PASS@rabbitmq:5672/
REDIS_URL=redis://:PASS@redis:6379/1   # другой Redis DB (0, 1, 2...)

# URL другого сервиса (если нужно обращаться к my-service)
MY_SERVICE_URL=http://my-service:8000
```

#### 5. Создаём базу данных

```bash
docker exec -it postgres psql -U postgres -c "CREATE DATABASE orders_db;"
```

#### 6. Пишем код, пушим в main — CI/CD деплоит автоматически

---

## 16. Межсервисное взаимодействие

### Синхронное (HTTP-запросы)

Сервисы видят друг друга по **имени контейнера** через сеть `internal`:

```python
# В order-service: вызов my-service
import httpx
from src.core.config import settings

async def get_item(item_id: str) -> dict:
    async with httpx.AsyncClient(
        base_url=settings.MY_SERVICE_URL,  # http://my-service:8000
        timeout=10.0
    ) as client:
        response = await client.get(f"/api/v1/items/{item_id}")
        response.raise_for_status()
        return response.json()
```

В `src/core/config.py` добавьте:
```python
MY_SERVICE_URL: str = "http://my-service:8000"
```

В `docker-compose.prod.yml` добавьте сеть `internal` если её нет.

> ⚠️ Прямые HTTP-вызовы между сервисами работают **только** если оба сервиса в одной сети `internal`

### Асинхронное (TaskIQ + RabbitMQ)

**Сервис-отправитель** публикует задачу в очередь:

```python
# В order-service: публикуем событие после создания заказа
from src.messaging.publishers import publish_to_other_service

await publish_to_other_service.kiq(
    event_type="order.created",
    payload={"order_id": str(order.id), "user_id": str(order.user_id)}
)
```

**Сервис-получатель** (my-service worker) подписан на очередь `my-service-events`:

```python
# В my-service: src/messaging/consumers/__init__.py
@broker.task(queue_name="my-service-events")
async def process_external_event(event_type: str, payload: dict) -> None:
    if event_type == "order.created":
        # Обрабатываем создание заказа
        print(f"Order created: {payload['order_id']}")
```

> Имена задач и очередей должны совпадать между сервисами

---

## 17. Полезные команды

### На сервере (в веб-консоли или SSH)

```bash
# ─── Просмотр состояния ────────────────────────────────────────────────────
docker ps                            # все запущенные контейнеры
docker ps -a                         # все контейнеры включая остановленные
docker stats                         # CPU/RAM в реальном времени

# ─── Логи ─────────────────────────────────────────────────────────────────
docker logs my-service --tail=100     # последние 100 строк
docker logs my-service -f             # логи в реальном времени
docker compose -f docker-compose.prod.yml logs -f   # все сервисы compose

# ─── Управление сервисами ──────────────────────────────────────────────────
docker restart my-service            # перезапустить контейнер
docker stop my-service               # остановить
docker start my-service              # запустить

# ─── Отладка: зайти в контейнер ───────────────────────────────────────────
docker exec -it my-service /bin/bash  # или /bin/sh если bash нет
docker exec -it my-service python -c "from src.core.config import settings; print(settings)"

# ─── Миграции вручную ─────────────────────────────────────────────────────
# Перейти в директорию сервиса на сервере
cd /opt/microservices/my-service

# Запустить миграции
IMAGE_NAME=ghcr.io/karpov-services/my-service IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml run --rm migrate

# ─── Обновить сервис вручную (без CI/CD) ──────────────────────────────────
cd /opt/microservices/my-service
docker login ghcr.io -u YOUR_GITHUB_USERNAME -p YOUR_GHCR_TOKEN
IMAGE_NAME=ghcr.io/karpov-services/my-service IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml pull
IMAGE_NAME=ghcr.io/karpov-services/my-service IMAGE_TAG=latest \
  docker compose -f docker-compose.prod.yml up -d --no-deps my-service my-service-worker

# ─── Инфраструктура ───────────────────────────────────────────────────────
cd /opt/microservices/infra
docker compose ps                    # статус infra сервисов
docker compose restart postgres      # перезапустить PostgreSQL
docker compose logs -f traefik       # логи Traefik

# ─── PostgreSQL ───────────────────────────────────────────────────────────
docker exec -it postgres psql -U postgres      # войти в psql
# Внутри psql:
# \l              — список баз данных
# \c mydb         — переключиться на базу
# \dt             — список таблиц
# SELECT * FROM items LIMIT 10;
# \q              — выйти

# ─── Очистка образов ──────────────────────────────────────────────────────
docker image prune -a -f             # удалить все неиспользуемые образы
docker system prune -f               # удалить контейнеры, сети, образы (осторожно!)
```

### В PowerShell (для работы с проектом локально)

```powershell
# Скопировать шаблон для нового сервиса
Copy-Item -Recurse "templates\microservice-template" "C:\projects\order-service"

# Быстро найти и заменить имя сервиса в файлах
Get-ChildItem "C:\projects\order-service" -Recurse -File |
  ForEach-Object {
    (Get-Content $_.FullName) -replace 'my-service', 'order-service' |
    Set-Content $_.FullName
  }
```

---

## 18. Чеклист

### ✅ Сервер (один раз)

- [ ] VPS создан на TimeWeb, Ubuntu 22.04
- [ ] Веб-консоль открывается, можно войти
- [ ] `docker --version` — Docker установлен
- [ ] `docker compose version` — Docker Compose установлен
- [ ] UFW настроен: порты 22, 80, 443, 8080, 9000, 15672 открыты
- [ ] DuckDNS: IP VPS прописан в `karpov1.duckdns.org` → update ip ✅
- [ ] Пароли сгенерированы и сохранены в надёжном месте

### ✅ Инфраструктура (один раз)

- [ ] `/opt/microservices/infra/.env` создан (`DOMAIN=karpov1.duckdns.org` + пароли)
- [ ] `/opt/microservices/infra/traefik.yml` создан (с вашим email для Let's Encrypt)
- [ ] `docker-compose.yml` инфраструктуры загружен
- [ ] Docker-сети созданы: `traefik-net`, `internal`
- [ ] `docker compose up -d` — все сервисы `healthy`
- [ ] `http://karpov1.duckdns.org:9000` — Portainer открывается, admin создан
- [ ] `http://karpov1.duckdns.org:15672` — RabbitMQ Management UI открывается
- [ ] `http://karpov1.duckdns.org:8080/dashboard/` — Traefik Dashboard открывается

### ✅ SSH-ключ для CI/CD (один раз)

- [ ] Ключ `/root/.ssh/github_deploy` создан
- [ ] Публичный ключ добавлен в `authorized_keys`
- [ ] Приватный ключ скопирован в GitHub Secret `SSH_PRIVATE_KEY`

### ✅ Для каждого микросервиса

- [ ] Репозиторий создан в организации `karpov-services` на GitHub
- [ ] Шаблон скопирован, `my-service` переименован
- [ ] `PathPrefix` в `docker-compose.prod.yml` обновлён
- [ ] Бизнес-логика написана (модели, схемы, сервисы)
- [ ] Секрет `SERVICE_DIR` добавлен в репозиторий на GitHub
- [ ] Org-секреты (`SSH_PRIVATE_KEY`, `VPS_HOST`, `VPS_USER`, `GHCR_TOKEN`, `GHCR_USER`) добавлены один раз
- [ ] База данных создана на сервере: `CREATE DATABASE service_db;`
- [ ] `/opt/microservices/service-name/.env.prod` создан
- [ ] Директория `/opt/microservices/service-name/` создана на сервере
- [ ] Коммит в `main` — GitHub Actions прошёл все 3 джобы (`test` → `build` → `deploy`)
- [ ] `docker ps` — контейнеры сервиса запущены
- [ ] API доступен: `https://karpov1.duckdns.org/api/v1/...`

---

## 📁 Файлы шаблонов в этом репозитории

```
templates/
├── infra/
│   ├── docker-compose.yml      ← инфраструктура сервера (Traefik, Postgres, Redis, RabbitMQ, Portainer)
│   ├── traefik.yml             ← конфигурация Traefik
│   └── .env.example            ← переменные инфраструктуры
│
└── microservice-template/
    ├── src/
    │   ├── main.py                   ← FastAPI приложение
    │   ├── core/
    │   │   ├── config.py             ← настройки (pydantic-settings)
    │   │   ├── lifespan.py           ← startup/shutdown
    │   │   ├── database/             ← engine, session, Base
    │   │   ├── exceptions/           ← кастомные исключения
    │   │   ├── logging/              ← setup_logging, get_logger
    │   │   ├── rabbitmq/             ← прямой RabbitMQ клиент (aio_pika)
    │   │   ├── redis/                ← Redis клиент
    │   │   └── taskiq/               ← брокер TaskIQ
    │   ├── api/
    │   │   ├── api_v1/               ← FastAPI роутеры
    │   │   ├── depends/              ← общие зависимости
    │   │   └── middlewares/          ← CORS и прочее
    │   ├── models/                   ← SQLAlchemy модели + миксины
    │   ├── repositories/             ← Generic BaseRepository
    │   ├── schemas/                  ← Pydantic схемы
    │   ├── services/                 ← бизнес-логика
    │   ├── messaging/
    │   │   ├── consumers/            ← TaskIQ задачи (обработчики)
    │   │   └── publishers/           ← публикация событий
    │   └── tests/                    ← тесты на SQLite (без внешних зависимостей)
    ├── alembic/env.py          ← async Alembic
    ├── Dockerfile              ← многоэтапная сборка
    ├── docker-compose.yml      ← локальная разработка
    ├── docker-compose.prod.yml         ← продакшн деплой (с SSL)
    ├── docker-compose.prod.no-ssl.yml  ← продакшн деплой без SSL
    ├── .github/workflows/deploy.yml    ← GitHub Actions CI/CD
    ├── pyproject.toml          ← зависимости
    └── .env.example            ← пример переменных
```

---

> 💡 **Совет:** Начните с одного сервиса (`my-service`) и пройдите весь цикл: локальная разработка → пуш в GitHub → GitHub Actions → деплой на VPS. После первого успешного деплоя добавляйте следующие сервисы — они настраиваются за 15–20 минут по той же схеме.

