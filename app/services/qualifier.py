import json
import logging
from openai import AsyncOpenAI

from app.models.lead import LeadRequest, QualificationResult, LeadStatus
from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Ты — ИИ-помощник для квалификации входящих лидов для freelance Python/AI разработчика.
Специализация разработчика: Telegram-боты, AI-агенты, FastAPI сервисы, автоматизация бизнес-процессов.
Стек: Python, FastAPI, aiogram, OpenAI/Claude API, SQLite/PostgreSQL, Docker.

Проанализируй лид и верни ТОЛЬКО валидный JSON без markdown-обёрток.

Формат ответа:
{
  "score": <0-100, общий скор>,
  "status": <"hot"|"warm"|"cold"|"unqualified">,
  "fit_score": <0-10, насколько задача подходит под специализацию>,
  "budget_score": <0-10, адекватность бюджета для задачи>,
  "urgency_score": <0-10, срочность и мотивация клиента>,
  "clarity_score": <0-10, чёткость и конкретность задачи>,
  "summary": "<2-3 предложения: кто клиент и что хочет>",
  "recommendation": "<конкретная рекомендация: написать сразу / уточнить бюджет / отказать / и т.д.>",
  "red_flags": ["<тревожный сигнал 1>", ...],
  "green_flags": ["<позитивный сигнал 1>", ...]
}

Логика скора:
- hot (75-100): чёткая задача + адекватный бюджет + срочность
- warm (50-74): задача понятна, но есть вопросы по бюджету или срокам
- cold (25-49): задача размытая или бюджет низкий
- unqualified (0-24): не по специализации или явно нецелевой лид
"""


def _build_user_message(lead: LeadRequest) -> str:
    parts = [
        f"Имя/компания: {lead.name}",
        f"Контакт: {lead.contact}",
        f"Описание задачи: {lead.task_description}",
    ]
    if lead.budget:
        parts.append(f"Бюджет: {lead.budget}")
    if lead.deadline:
        parts.append(f"Срок: {lead.deadline}")
    return "\n".join(parts)


async def qualify_lead(lead: LeadRequest) -> QualificationResult:
    """Отправляет лид в OpenAI и возвращает структурированный результат квалификации."""
    client = AsyncOpenAI(
        api_key=settings.openai_api_key,
        base_url=settings.openai_base_url,
    )

    user_message = _build_user_message(lead)
    logger.info("Qualifying lead: %s", lead.name)

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
    except Exception as exc:
        logger.error("OpenAI API error: %s", exc)
        raise RuntimeError(f"Ошибка обращения к AI: {exc}") from exc

    raw = response.choices[0].message.content or ""
    logger.debug("Raw AI response: %s", raw)

    # Убираем возможные markdown-блоки
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        cleaned = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse AI JSON: %s\nRaw: %s", exc, raw)
        raise ValueError(f"AI вернул невалидный JSON: {exc}") from exc

    # Нормализуем статус
    status_raw = data.get("status", "cold")
    try:
        status = LeadStatus(status_raw)
    except ValueError:
        status = LeadStatus.COLD

    return QualificationResult(
        score=int(data.get("score", 0)),
        status=status,
        fit_score=int(data.get("fit_score", 0)),
        budget_score=int(data.get("budget_score", 0)),
        urgency_score=int(data.get("urgency_score", 0)),
        clarity_score=int(data.get("clarity_score", 0)),
        summary=data.get("summary", ""),
        recommendation=data.get("recommendation", ""),
        red_flags=data.get("red_flags", []),
        green_flags=data.get("green_flags", []),
    )
