import logging
import httpx

from app.models.lead import LeadResponse, LeadStatus
from app.config import settings

logger = logging.getLogger(__name__)

STATUS_EMOJI = {
    LeadStatus.HOT: "🔥",
    LeadStatus.WARM: "🌤",
    LeadStatus.COLD: "❄️",
    LeadStatus.UNQUALIFIED: "🚫",
}


def _format_message(lead: LeadResponse) -> str:
    q = lead.qualification
    emoji = STATUS_EMOJI.get(q.status, "📋")
    flags_red = "\n".join(f"  ⚠️ {f}" for f in q.red_flags) if q.red_flags else "  —"
    flags_green = "\n".join(f"  ✅ {f}" for f in q.green_flags) if q.green_flags else "  —"

    return (
        f"{emoji} *Новый лид: {lead.name}*\n"
        f"Контакт: `{lead.contact}`\n\n"
        f"📊 Скор: *{q.score}/100* | Статус: *{q.status.upper()}*\n"
        f"└ Ниша: {q.fit_score}/10 | Бюджет: {q.budget_score}/10 | "
        f"Срочность: {q.urgency_score}/10 | Чёткость: {q.clarity_score}/10\n\n"
        f"📝 *Резюме:* {q.summary}\n\n"
        f"💡 *Рекомендация:* {q.recommendation}\n\n"
        f"🚩 *Тревожные сигналы:*\n{flags_red}\n\n"
        f"✨ *Позитивные сигналы:*\n{flags_green}\n\n"
        f"🆔 ID: `{lead.lead_id}`"
    )


async def notify_telegram(lead: LeadResponse) -> None:
    """Отправляет уведомление о новом лиде в Telegram. Не бросает исключение при ошибке."""
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.debug("Telegram notifications not configured, skipping")
        return

    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": _format_message(lead),
        "parse_mode": "Markdown",
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
        logger.info("Telegram notification sent for lead %s", lead.lead_id)
    except Exception as exc:
        logger.warning("Failed to send Telegram notification: %s", exc)
