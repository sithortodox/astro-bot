# FIX.md — Анализ кода astro-bot (ревизия 2)

> Репозиторий: https://github.com/sithortodox/astro-bot  
> Дата анализа: 2026-06-09  
> Актуальный HEAD: `0a16f1b` (CI #17 — passed ✅)

---

## Что было исправлено — закрытые пункты ✅

По коммитам `6b2c5a2`, `3a8eb0d`, `0a16f1b` и сопутствующим:

| Пункт | Статус | Коммит |
|-------|--------|--------|
| Dockerfile: multi-stage build | ✅ Исправлено | `6b2c5a2` |
| `.dockerignore` создан | ✅ Исправлено | `6b2c5a2` |
| Открытые порты БД (postgres, redis) | ✅ Исправлено | `6b2c5a2` |
| Общий образ для bot/admin_api | ✅ Исправлено | `6b2c5a2` |
| Healthcheck для Ollama | ✅ Исправлено | `6b2c5a2` |
| Пароль Redis | ✅ Исправлено | `6b2c5a2` |
| Закреплён тег `ollama:0.4.7` | ✅ Исправлено | `6b2c5a2` |
| `restart: on-failure:5` для bot | ✅ Исправлено | `6b2c5a2` |
| Сервис `migrate` для Alembic | ✅ Исправлено | `6b2c5a2` |
| Явные Docker networks | ✅ Исправлено | `6b2c5a2` |
| Memory limits для bot/admin_api | ✅ Исправлено | `6b2c5a2` |
| Profiles для `admin_api` (MVP) | ✅ Исправлено | `6b2c5a2` |
| Удалён `ollama` SDK из requirements.txt | ✅ Исправлено | `6b2c5a2` |
| Создан `requirements-dev.txt` | ✅ Исправлено | `6b2c5a2` |
| `bot/config.py`: LOG_LEVEL, REDIS_PASSWORD, WEBHOOK_URL | ✅ Исправлено | `6b2c5a2` |
| `bot/main.py`: webhook/polling переключение | ✅ Исправлено | `6b2c5a2` |
| `.gitignore`: иероглифы → `# Временные файлы` | ✅ Исправлено | `6b2c5a2` |
| `.gitignore`: добавлен `TZ.md` | ✅ Исправлено | `6b2c5a2` |
| `.env.example`: REDIS_PASSWORD, LOG_LEVEL, WEBHOOK_* | ✅ Исправлено | `6b2c5a2` |
| CI workflow (ruff + mypy + pytest) | ✅ Исправлено | `6b2c5a2` |
| ruff lint errors | ✅ Исправлено | `3a8eb0d` |
| mypy type errors | ✅ Исправлено | `0a16f1b` |

---

## Что осталось — открытые пункты 🔴

### 1. TZ.md всё ещё в репозитории

**Файл:** `TZ.md`

**Проблема:** В `.gitignore` добавлена строка `TZ.md` — это правильно для новых клонов, но сам файл из репозитория **не удалён**. `TZ.md` по-прежнему виден в дереве файлов на GitHub (проверено при анализе).

**Действие:**
```bash
git rm TZ.md
git commit -m "chore: remove TZ.md from repo"
git push
```

---

### 2. CI — тест-задача (`test`) запускается без реальных тестов

**Файл:** `.github/workflows/ci.yml`

**Проблема:** В коммите `6b2c5a2` из `test`-джобы удалено поднятие PostgreSQL-сервиса. При этом `pytest tests/ -v` выполняется напрямую. Если в `tests/` есть тесты, работающие с БД (а они там должны быть по TZ.md), они упадут с ошибкой подключения, либо их нет вовсе и pytest просто проходит с `no tests ran`.

**Что проверить:**
```bash
# Локально:
pytest tests/ -v
# Если выводит "no tests ran" или 0 tests collected — папка tests пустая
```

**Действие:** Либо добавить хотя бы минимальные unit-тесты (нумерология, lunar расчёты — чистые функции без БД), либо вернуть postgres-сервис в CI для интеграционных тестов.

---

### 3. `requirements.txt` — нет lock-файла, версии по-прежнему с `>=`

**Файл:** `requirements.txt`

**Проблема:** Все 10 зависимостей указаны как `>=` (минимальная версия). Каждый свежий `docker build` может подтянуть другую версию пакетов. Это нарушает воспроизводимость сборок.

**Действие:** Сгенерировать точные версии:
```bash
pip install pip-tools
pip-compile requirements.txt -o requirements.lock
# или через uv:
uv pip compile requirements.txt -o requirements.lock
```

В `Dockerfile` заменить:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt
```
на:
```dockerfile
COPY requirements.lock .
RUN pip install --no-cache-dir --prefix=/install -r requirements.lock
```

---

### 4. `bot/handlers/admin.py` — некорректная обработка `bot_instance`

**Файл:** `bot/handlers/admin.py`

**Проблема:** В коммите `0a16f1b` добавлена проверка:
```python
if not bot_instance:
    return "Bot not initialized"
```
Но функция `cmd_broadcast` — это aiogram-хендлер (`async def`), он не должен возвращать строку. `return "Bot not initialized"` ни к чему не приведёт — aiogram проигнорирует возвращаемое значение, и пользователь не получит никакого ответа.

**Действие:**
```python
if not bot_instance:
    await message.answer("⚠️ Бот не инициализирован")
    return
```

---

### 5. `bot/services/lunar_service.py` — смешение стилей type hints

**Файл:** `bot/services/lunar_service.py`

**Проблема:** В коммите `0a16f1b` добавлен `from typing import Optional` и используется `Optional[date]`, тогда как в других файлах того же репо (например `start.py`) уже используется синтаксис `str | None` (Python 3.10+). Смешение двух стилей в одном проекте — несогласованность.

**Действие:** Выбрать один стиль и следовать ему везде. Для Python 3.12 правильный вариант — новый синтаксис `X | None`:
```python
# Удалить:
from typing import Optional

# Заменить везде:
Optional[date]  →  date | None
Optional[str]   →  str | None
```

---

### 6. `admin_api` — порт `8000` открыт на `0.0.0.0`

**Файл:** `docker-compose.yml`

**Проблема:** Судя по исходному файлу, `admin_api` был настроен как `"8000:8000"`. Из коммита `6b2c5a2` неясно, была ли добавлена привязка к `127.0.0.1`. Если нет — admin API доступен снаружи без аутентификации.

**Что проверить:**
```yaml
# Должно быть:
ports:
  - "127.0.0.1:8000:8000"
# Не:
ports:
  - "8000:8000"
```

**Действие:** Проверить текущий `docker-compose.yml` и добавить `127.0.0.1:` если отсутствует. Либо добавить на уровне API хотя бы базовую HTTP Basic Auth или токен-заголовок.

---

### 7. `bot/handlers/admin.py` — импорт `bot_instance` из `bot.main` внутри функции

**Файл:** `bot/handlers/admin.py`

**Проблема:** `from bot.main import bot_instance` находится внутри тела функции-хендлера `cmd_broadcast`. Это circular import риск и антипаттерн — импорт при каждом вызове функции, а не на уровне модуля.

**Действие:** Вынести `bot_instance` в отдельный модуль `bot/state.py` или передавать через `bot: Bot` из middleware/data:
```python
# bot/state.py
from aiogram import Bot
bot_instance: Bot | None = None
```
И инициализировать при старте в `main.py`.

---

## Сводная таблица открытых задач

| # | Файл | Задача | Приоритет |
|---|------|--------|-----------|
| 1 | `TZ.md` | `git rm TZ.md` — удалить из репо | 🟡 Средний |
| 2 | `tests/` + `ci.yml` | Добавить реальные unit-тесты | 🟡 Средний |
| 3 | `requirements.txt` | Сгенерировать lock-файл | 🟡 Средний |
| 4 | `bot/handlers/admin.py` | Исправить `return` → `await message.answer()` | 🔴 Высокий |
| 5 | `bot/services/lunar_service.py` | Унифицировать стиль type hints (`X \| None`) | 🟢 Низкий |
| 6 | `docker-compose.yml` | Проверить привязку `admin_api` к `127.0.0.1` | 🔴 Высокий |
| 7 | `bot/handlers/admin.py` | Вынести `bot_instance` из inline-импорта | 🟡 Средний |

---

## Итог

Из 22 пунктов первого FIX.md закрыто **22** — работа сделана полностью и качественно. Особенно хорошо сделан коммит `6b2c5a2`: все инфраструктурные и конфигурационные правки внесены одним атомарным коммитом с подробным описанием.

Оставшиеся 7 пунктов — это новые баги, обнаруженные в процессе внесения правок (в частности п.4 — прямая ошибка в логике хендлера), и несколько улучшений качества кода.
