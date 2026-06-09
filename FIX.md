# FIX.md — Техническое задание на исправление кода astro-bot

> Репозиторий: https://github.com/sithortodox/astro-bot  
> Дата анализа: 2026-06-09  
> Статус проекта: MVP в разработке

---

## Обзор проблем

По результатам анализа файлов (README, TZ.md, Dockerfile, docker-compose.yml, requirements.txt, .env.example, .gitignore) выявлены проблемы четырёх категорий: **ошибки конфигурации**, **избыточность**, **оптимизация**, **улучшения по работе**.

---

## 1. ОШИБКИ — обязательные исправления

### 1.1 Dockerfile — отсутствует multi-stage build и `.dockerignore`

**Файл:** `Dockerfile`

**Проблема:** Однослойный образ копирует весь контекст включая `tests/`, `scripts/`, `.git/`. Образ раздут. Нет `.dockerignore`.

**Текущее состояние:**
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "-m", "bot.main"]
```

**Исправление — заменить на multi-stage:**
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY bot/ ./bot/
COPY api/ ./api/
COPY knowledge_base/ ./knowledge_base/
CMD ["python", "-m", "bot.main"]
```

**Создать файл `.dockerignore`:**
```
.git/
.github/
tests/
scripts/
*.md
.env
.env.*
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

---

### 1.2 docker-compose.yml — открытые порты БД в продакшене

**Файл:** `docker-compose.yml`

**Проблема:** PostgreSQL (5432) и Redis (6379) проброшены на хост (`0.0.0.0`). На VPS это открывает порты наружу — прямая угроза безопасности.

**Исправление:** Убрать `ports` у postgres и redis. Сервисы в сети Docker общаются по именам без проброса.

```yaml
postgres:
  # УДАЛИТЬ блок ports полностью

redis:
  # УДАЛИТЬ блок ports полностью

admin_api:
  ports:
    - "127.0.0.1:8000:8000"  # только localhost, не 0.0.0.0
```

---

### 1.3 docker-compose.yml — `admin_api` собирает отдельный образ из того же Dockerfile

**Файл:** `docker-compose.yml`

**Проблема:** `admin_api` дублирует build того же кода. Два одинаковых образа — лишний расход дискового места и времени CI.

**Исправление:** Использовать общий образ:

```yaml
bot:
  image: astro-bot:latest
  build:
    context: .
    dockerfile: Dockerfile
  # ...

admin_api:
  image: astro-bot:latest  # тот же образ, без повторного build
  command: uvicorn api.admin:app --host 0.0.0.0 --port 8000
  # ...
```

---

### 1.4 requirements.txt — расхождение с TZ.md

**Файл:** `requirements.txt` vs `TZ.md` (раздел 17)

**Проблема:** В `TZ.md` перечислены `requests>=2.31.0` и `beautifulsoup4>=4.12.0`. В `requirements.txt` их нет. Скрипт `scripts/parse_tarot.py` не запустится.

**Исправление:** Вынести скриптовые зависимости в `requirements-dev.txt`:
```
# requirements-dev.txt
requests>=2.31.0
beautifulsoup4>=4.12.0
pytest>=8.0.0
ruff>=0.4.0
mypy>=1.10.0
```

И убрать из основного `requirements.txt` — они не нужны в Docker-образе бота.

---

### 1.5 docker-compose.yml — Ollama без healthcheck

**Файл:** `docker-compose.yml`

**Проблема:** `bot` зависит от `ollama` через `condition: service_started`, но Ollama стартует медленно. Бот будет падать при первых AI-запросах.

**Исправление:**
```yaml
ollama:
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:11434/api/tags || exit 1"]
    interval: 10s
    timeout: 10s
    retries: 10
    start_period: 60s

bot:
  depends_on:
    ollama:
      condition: service_healthy  # вместо service_started
```

---

### 1.6 .gitignore — комментарий с китайскими иероглифами

**Файл:** `.gitignore`, строка 53

**Проблема:** `#临时 файлы` — артефакт AI-генерации.

**Исправление:** Заменить на `# Временные файлы`.

---

## 2. ЛИШНЕЕ — удалить

### 2.1 TZ.md в корне репозитория

**Файл:** `TZ.md`

**Проблема:** Документ планирования в публичном репо раскрывает внутренние решения, планы монетизации, VPS-бюджет. В репо достаточно `README.md`.

**Действие:** Удалить `TZ.md`. Перенести в приватный документ. Добавить в `.gitignore`:
```
TZ.md
```

---

### 2.2 Дублирование: `ollama` SDK + `httpx`

**Файл:** `requirements.txt`

**Проблема:** `ollama>=0.3.0` (Python SDK) и `httpx>=0.27.0` оба присутствуют. TZ.md описывает интеграцию как `httpx → localhost:11434`. Это дублирование.

**Действие:** Определить один способ:
- Рекомендуется оставить только `httpx`, удалить `ollama` SDK — меньше зависимостей, прямой контроль над запросами.

---

### 2.3 `admin_api` в docker-compose для MVP

**Файл:** `docker-compose.yml`

**Проблема:** TZ.md явно указывает: MVP без веб-панели. Отдельный сервис усложняет деплой и ест RAM.

**Действие:** Добавить profile, чтобы сервис не запускался по умолчанию:
```yaml
admin_api:
  profiles: ["admin"]
  # запуск: docker-compose --profile admin up
```

---

## 3. ОПТИМИЗАЦИЯ

### 3.1 Закрепить версию образа Ollama

**Файл:** `docker-compose.yml`

**Проблема:** `ollama/ollama:latest` — нестабильный тег, обновление может сломать продакшен.

**Исправление:**
```yaml
ollama:
  image: ollama/ollama:0.4.7  # закрепить актуальную стабильную версию
```

---

### 3.2 Изменить `restart: unless-stopped` на `on-failure` для bot

**Файл:** `docker-compose.yml`

**Проблема:** `unless-stopped` перезапускает даже при фатальных ошибках (неверный токен), создавая бесконечный цикл.

**Исправление:**
```yaml
bot:
  restart: on-failure:5
```

---

### 3.3 Lock-файл зависимостей

**Файл:** `requirements.txt`

**Проблема:** Все версии `>=` — сборка не воспроизводима. Разные установки могут получить разные версии пакетов.

**Рекомендуемый подход:**
1. Переименовать текущий в `requirements.in` (абстрактные зависимости с `>=`).
2. Сгенерировать `requirements.txt` через `pip-compile` (пакет `pip-tools`) — точные версии.
3. В `Dockerfile` использовать точный `requirements.txt`.

---

### 3.4 Пароль для Redis

**Файл:** `docker-compose.yml`

**Проблема:** Redis без аутентификации — вектор атаки при любой уязвимости в сети Docker.

**Исправление:**
```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  environment:
    - REDIS_PASSWORD=${REDIS_PASSWORD}
```

В `.env.example`:
```
REDIS_PASSWORD=CHANGE_ME
```

Обновить `REDIS_URL` везде:
```
REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0
```

---

### 3.5 Явные Docker networks

**Файл:** `docker-compose.yml`

**Проблема:** Все сервисы в дефолтной сети без изоляции.

**Исправление:**
```yaml
networks:
  backend:
  frontend:

services:
  postgres:
    networks: [backend]
  redis:
    networks: [backend]
  bot:
    networks: [backend]
  ollama:
    networks: [backend]
  admin_api:
    networks: [backend, frontend]
```

---

## 4. УЛУЧШЕНИЯ ПО РАБОТЕ

### 4.1 Создать GitHub Actions CI workflow

**Файл:** `.github/workflows/ci.yml` — отсутствует (упомянут в TZ.md, но не реализован)

**Создать:**
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install ruff mypy
      - run: ruff check .
      - run: mypy bot/ api/ --ignore-missing-imports

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: pytest tests/ -v
```

---

### 4.2 Добавить отдельный сервис для Alembic-миграций

**Файл:** `docker-compose.yml`

**Проблема:** Непонятно, кто запускает `alembic upgrade head`. Если это делает `bot` при старте — порядок запуска `admin_api` не гарантирован.

**Исправление:**
```yaml
migrate:
  image: astro-bot:latest
  command: alembic upgrade head
  depends_on:
    postgres:
      condition: service_healthy
  restart: "no"

bot:
  depends_on:
    migrate:
      condition: service_completed_successfully
    # ...

admin_api:
  depends_on:
    migrate:
      condition: service_completed_successfully
    # ...
```

---

### 4.3 Добавить переменные в `.env.example`

**Файл:** `.env.example`

**Добавить:**
```
# Уровень логирования
LOG_LEVEL=INFO

# Пароль Redis (см. docker-compose.yml)
REDIS_PASSWORD=CHANGE_ME

# Webhook-режим для продакшена (оставить пустым для polling/разработки)
WEBHOOK_URL=
WEBHOOK_SECRET=
```

Соответственно обновить `bot/config.py` с полями `log_level`, `redis_password`, `webhook_url`, `webhook_secret`.

---

### 4.4 Добавить лимиты памяти для bot и admin_api

**Файл:** `docker-compose.yml`

**Проблема:** Только `ollama` имеет `memory: 4G`. Бот без лимитов при утечке памяти может убить Ollama.

**Исправление:**
```yaml
bot:
  deploy:
    resources:
      limits:
        memory: 512M
      reservations:
        memory: 128M

admin_api:
  deploy:
    resources:
      limits:
        memory: 256M
```

---

### 4.5 Webhook vs Polling — явное переключение в коде

**Файл:** `bot/main.py`

**Проблема:** Для продакшена на VPS webhook значительно эффективнее polling (меньше задержка, нет лишних TCP-сессий к Telegram API). Нужна явная логика переключения.

**Паттерн в `bot/main.py`:**
```python
async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    # ... регистрация роутеров ...

    if settings.webhook_url:
        # Продакшен: webhook
        await bot.set_webhook(
            url=f"{settings.webhook_url}/webhook",
            secret_token=settings.webhook_secret,
        )
        # запуск aiohttp/uvicorn сервера
    else:
        # Разработка: polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
```

---

## Сводная таблица задач

| # | Категория | Файл | Задача | Приоритет |
|---|-----------|------|--------|-----------|
| 1.1 | 🔴 Ошибка | `Dockerfile` | Multi-stage build + `.dockerignore` | Высокий |
| 1.2 | 🔴 Ошибка | `docker-compose.yml` | Убрать открытые порты БД | Высокий |
| 1.3 | 🟡 Ошибка | `docker-compose.yml` | Общий образ для bot/admin_api | Средний |
| 1.4 | 🟡 Ошибка | `requirements.txt` | Вынести dev-зависимости | Средний |
| 1.5 | 🔴 Ошибка | `docker-compose.yml` | Healthcheck для Ollama | Высокий |
| 1.6 | 🟢 Ошибка | `.gitignore` | Исправить иероглифы | Низкий |
| 2.1 | 🟡 Лишнее | `TZ.md` | Удалить из репозитория | Средний |
| 2.2 | 🟡 Лишнее | `requirements.txt` | Убрать дублирование ollama/httpx | Средний |
| 2.3 | 🟢 Лишнее | `docker-compose.yml` | Profiles для admin_api | Низкий |
| 3.1 | 🟡 Оптим. | `docker-compose.yml` | Закрепить тег ollama | Средний |
| 3.2 | 🟡 Оптим. | `docker-compose.yml` | `restart: on-failure:5` для bot | Средний |
| 3.3 | 🟡 Оптим. | `requirements.txt` | Lock-файл зависимостей | Средний |
| 3.4 | 🔴 Оптим. | `docker-compose.yml` | Пароль для Redis | Высокий |
| 3.5 | 🟢 Оптим. | `docker-compose.yml` | Явные Docker networks | Низкий |
| 4.1 | 🟡 Улучш. | `.github/workflows/` | CI workflow | Средний |
| 4.2 | 🟡 Улучш. | `docker-compose.yml` | Сервис migrate | Средний |
| 4.3 | 🟢 Улучш. | `.env.example` | Новые переменные | Низкий |
| 4.4 | 🟡 Улучш. | `docker-compose.yml` | Memory limits | Средний |
| 4.5 | 🟡 Улучш. | `bot/main.py` | Webhook/polling переключение | Средний |

---

## Рекомендуемый порядок выполнения

**Шаг 1 — Безопасность (немедленно):**  
1.2 → 3.4 → 1.5

**Шаг 2 — Сборка:**  
1.1 → 1.3 → 4.2 → 3.1 → 3.2

**Шаг 3 — Зависимости:**  
1.4 → 2.2 → 3.3

**Шаг 4 — Конфигурация:**  
4.3 → 4.5

**Шаг 5 — CI и качество:**  
4.1 → 4.4 → 3.5 → 2.1 → 2.3 → 1.6
