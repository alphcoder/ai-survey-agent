# 🎙 AI Survey Agent

AI-платформа для автоматизированных интервью и исследований — **FastAPI** + **PostgreSQL** + **OpenAI GPT**.

AI-агент проводит глубинные интервью с респондентами: задаёт вопросы, адаптируется к ответам, генерирует саммари и инсайты. Для маркетинговых и продуктовых исследований.

## Архитектура

```
┌────────────────────────┐
│   React Frontend       │
│   ├─ Создание опросов  │
│   ├─ Чат-интерфейс     │
│   └─ Аналитика         │
└───────────┬────────────┘
            │ REST API
┌───────────▼────────────┐
│   FastAPI Backend      │
│   ├─ /api/surveys      │  CRUD опросов
│   ├─ /api/interviews   │  Сессии + сообщения
│   └─ agents/           │
│       └─ interviewer   │  AI-агент
└───────────┬────────────┘
            │
     ┌──────▼──────┐     ┌──────────────┐
     │ PostgreSQL  │     │  OpenAI API  │
     │ surveys     │     │  GPT-4o      │
     │ sessions    │     │  JSON mode   │
     │ messages    │     └──────────────┘
     └─────────────┘
```

## Как работает AI-агент

1. Исследователь создаёт опрос с целью и параметрами
2. Респондент открывает ссылку — агент задаёт первый вопрос
3. Агент анализирует ответ и адаптирует следующий вопрос
4. После N вопросов — автоматический summary + инсайты (JSON mode)

Агент учитывает:
- Цель исследования (задаётся при создании опроса)
- Историю диалога (контекст всех предыдущих ответов)
- Глубину ответа (задаёт уточняющие вопросы при поверхностных ответах)

## Стек

| Компонент | Технология |
|-----------|------------|
| Backend | Python 3.12, FastAPI, async/await |
| ORM | SQLAlchemy 2.0 (async), asyncpg |
| БД | PostgreSQL (UUID, JSONB) |
| AI | OpenAI API (GPT-4o, JSON mode) |
| Валидация | Pydantic v2 |
| Frontend | React (планируется) |

## API

| Метод | URL | Описание |
|-------|-----|----------|
| GET | /api/surveys | Список опросов |
| POST | /api/surveys | Создать опрос (title, goal, max_questions) |
| GET | /api/surveys/:id/analytics | Аналитика по опросу |
| POST | /api/interviews/start | Начать интервью |
| POST | /api/interviews/:id/message | Отправить ответ → получить вопрос |
| GET | /api/interviews/:id | Получить сессию с сообщениями |

## Быстрый старт

```bash
git clone https://github.com/alphcoder/ai-survey-agent.git
cd ai-survey-agent/backend

cp .env.example .env
# Заполнить OPENAI_API_KEY

pip install -r requirements.txt
uvicorn app.main:app --reload

# Swagger UI: http://localhost:8000/docs
```

## Структура

```
ai-survey-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI + CORS + startup
│   │   ├── config.py            # Pydantic Settings
│   │   ├── database.py          # AsyncSession + engine
│   │   ├── models/
│   │   │   └── survey.py        # Survey, InterviewSession, Message
│   │   ├── api/
│   │   │   ├── surveys.py       # CRUD + analytics
│   │   │   └── interviews.py    # Start, message, summary
│   │   └── agents/
│   │       └── interviewer.py   # AI-агент (generate_question, summary)
│   ├── requirements.txt
│   └── .env.example
└── README.md
```

## Лицензия

MIT
