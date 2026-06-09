# Astro Bot

Telegram-бот с астрологическими услугами: расклады Таро, нумерология, гороскопы, лунные рекомендации.

## Features

- **Tarot Readings**: Card of the day, 1-card and 3-card spreads
- **Numerology**: Life path, destiny, and personality numbers
- **Horoscopes**: Daily zodiac horoscopes
- **Lunar Services**: Moon phases, calendar, recommendations
- **AI Adaptation**: Personalized text via local LLM (Ollama + gemma3:4b)
- **Premium System**: Telegram Stars payments, subscriptions
- **Admin Panel**: User management, statistics, broadcast

## Tech Stack

- Python 3.12+
- aiogram 3.x (Telegram Bot)
- FastAPI (Admin API)
- PostgreSQL (database)
- Redis (caching)
- Ollama + gemma3:4b (AI text adaptation)
- ephem (lunar calculations)
- Docker + Docker Compose

## Quick Start

### 1. Clone repository

```bash
git clone https://github.com/sithortodox/astro-bot.git
cd astro-bot
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

Required settings:
- `BOT_TOKEN` - Telegram bot token from @BotFather
- `ADMIN_IDS` - Comma-separated Telegram user IDs for admin access

### 3. Start with Docker

```bash
docker-compose up -d
```

### 4. Check status

```bash
docker-compose ps
docker-compose logs bot
```

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Register and see welcome message |
| `/tarot` | Card of the day |
| `/tarot1` | One card reading (detailed) |
| `/tarot3` | Three card reading (Past/Present/Future) |
| `/numerology` | Life path, destiny, personality numbers |
| `/horoscope` | Daily horoscope |
| `/lunar` | Lunar phase and recommendations |
| `/setzodiac` | Set your zodiac sign |
| `/setbirth DD.MM.YYYY` | Set birth date |
| `/profile` | View your profile |
| `/history` | Request history |
| `/premium` | View/upgrade subscription |
| `/help` | List all commands |

### Admin Commands

| Command | Description |
|---------|-------------|
| `/admin` | Admin panel |
| `/stats` | Bot statistics |
| `/users` | List users |
| `/broadcast <text>` | Send message to all users |
| `/ban <user_id>` | Ban user |
| `/setpremium <user_id>` | Grant premium |

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/api/stats` | GET | Statistics |
| `/api/users` | GET | User list |
| `/api/user/{id}` | GET | User details |
| `/api/payments` | GET | Payment history |

## Project Structure

```
astro-bot/
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py            # Settings
│   ├── database.py          # SQLAlchemy async
│   ├── handlers/            # Command handlers
│   ├── services/            # Business logic
│   ├── middlewares/          # Middleware
│   └── models/              # Database models
├── api/
│   └── admin.py             # FastAPI admin API
├── knowledge_base/          # Tarot cards JSON
├── scripts/                 # Utility scripts
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

## Monetization

- **Free**: 1 request per day
- **Premium Monthly**: 100 Telegram Stars / 199 RUB
- **Premium Yearly**: 900 Telegram Stars / 1790 RUB

## License

MIT
