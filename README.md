# AI Lead Qualifier API

FastAPI сервис квалификации входящих лидов с помощью ИИ.

Когда клиент пишет «нужен бот» — непонятно: горячий это лид или спам. Сервис прогоняет описание задачи через GPT-4o-mini и за секунды выдаёт структурированный анализ: скор, статус, тревожные сигналы и конкретную рекомендацию.

## Стек

- **Python 3.12** + **FastAPI** + **Pydantic v2**
- **OpenAI API** через [ProxyAPI](https://proxyapi.ru/) (работает в России без VPN)
- **SQLite** — хранение всех лидов и результатов
- **Docker** — один контейнер, готов к деплою на VPS

## Что умеет

| Эндпоинт | Метод | Описание |
|---|---|---|
| `/leads/qualify` | POST | Квалифицировать новый лид через ИИ |
| `/leads/` | GET | История всех лидов (с пагинацией) |
| `/leads/{id}` | GET | Получить лид по ID |
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI с примерами |

### Пример ответа `/leads/qualify`

```json
{
  "lead_id": "f47ac10b-...",
  "name": "ООО Ромашка",
  "contact": "@ivan_tg",
  "qualification": {
    "score": 84,
    "status": "hot",
    "fit_score": 9,
    "budget_score": 8,
    "urgency_score": 8,
    "clarity_score": 9,
    "summary": "E-commerce компания хочет автоматизировать приём заявок через Telegram.",
    "recommendation": "Написать сегодня — чёткое ТЗ, бюджет адекватный, срочно.",
    "red_flags": [],
    "green_flags": ["Чёткое ТЗ", "Адекватный бюджет", "Срочно нужно"]
  },
  "created_at": "2025-06-10T12:00:00+00:00"
}
```

## Быстрый старт

### 1. Клонировать и настроить

```bash
git clone https://github.com/KirillTomenko/ai-lead-qualifier.git
cd ai-lead-qualifier
cp .env.example .env
```

Открыть `.env` и вставить ключ ProxyAPI:

```env
OPENAI_API_KEY=your-proxyapi-key-here
```

Ключ ProxyAPI получить на [proxyapi.ru](https://proxyapi.ru/).

### 2. Запустить через Docker (рекомендуется)

```bash
docker compose up --build
```

API будет доступно на `http://localhost:8000`.  
Swagger UI: `http://localhost:8000/docs`

### 3. Локальный запуск без Docker

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS

pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Тесты

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

10 тестов, покрытие: модели, API эндпоинты, валидация.

## Деплой на сервер через Docker Hub

### Сборка и публикация образа

```bash
# Сборка
docker build -t ai-lead-qualifier .

# Тег для Docker Hub
docker tag ai-lead-qualifier YOUR_DOCKERHUB_USERNAME/ai-lead-qualifier:latest

# Логин и пуш
docker login
docker push YOUR_DOCKERHUB_USERNAME/ai-lead-qualifier:latest
```

### Запуск на VPS

```bash
# Подключиться по SSH
ssh user@your-server-ip

# Установить Docker (Ubuntu)
curl -fsSL https://get.docker.com | sh

# Запустить контейнер
docker run -d \
  --name ai-lead-qualifier \
  --restart unless-stopped \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -v $(pwd)/data:/app/data \
  YOUR_DOCKERHUB_USERNAME/ai-lead-qualifier:latest
```

### Проверка работы

```bash
curl http://your-server-ip:8000/health

curl -X POST http://your-server-ip:8000/leads/qualify \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Тестовый клиент",
    "contact": "@test",
    "task_description": "Нужен Telegram-бот для приёма заявок с уведомлениями менеджеру",
    "budget": "50000 руб",
    "deadline": "2 недели"
  }'
```

## Telegram-уведомления (опционально)

При квалификации нового лида сервис может отправлять карточку в Telegram.

Добавить в `.env`:

```env
TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

Получить `TELEGRAM_CHAT_ID` можно через `@userinfobot`.

## Структура проекта

```
ai-lead-qualifier/
├── app/
│   ├── main.py              # FastAPI приложение, lifespan
│   ├── config.py            # Настройки через pydantic-settings
│   ├── models/
│   │   └── lead.py          # Pydantic модели (LeadRequest, LeadResponse, ...)
│   ├── routers/
│   │   ├── leads.py         # POST /qualify, GET /leads
│   │   └── health.py        # GET /health
│   └── services/
│       ├── qualifier.py     # Логика AI-квалификации (OpenAI)
│       ├── storage.py       # SQLite: сохранение и чтение лидов
│       └── notifier.py      # Telegram-уведомления
├── tests/
│   ├── test_models.py       # Тесты Pydantic моделей
│   └── test_api.py          # Интеграционные тесты API
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── requirements-dev.txt
```

## Автор

**Kirill Tomenko** — Python developer, AI agents & automation  
GitHub: [@KirillTomenko](https://github.com/KirillTomenko)  
Telegram-канал: [@kirill_ai_lab](https://t.me/kirill_ai_lab)
