import uuid
import logging
from fastapi import APIRouter, HTTPException, Query

from app.models.lead import LeadRequest, LeadResponse
from app.services.qualifier import qualify_lead
from app.services.storage import save_lead, get_lead_by_id, get_all_leads
from app.services.notifier import notify_telegram

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/leads", tags=["leads"])


@router.post(
    "/qualify",
    response_model=LeadResponse,
    status_code=201,
    summary="Квалифицировать новый лид",
    description=(
        "Принимает данные лида, прогоняет через AI-квалификатор, "
        "сохраняет результат и отправляет уведомление в Telegram (если настроен)."
    ),
)
async def qualify_lead_endpoint(lead: LeadRequest) -> LeadResponse:
    try:
        qualification = await qualify_lead(lead)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    lead_id = str(uuid.uuid4())
    created_at = save_lead(
        lead_id=lead_id,
        name=lead.name,
        contact=lead.contact,
        task=lead.task_description,
        budget=lead.budget,
        deadline=lead.deadline,
        result=qualification,
    )

    response = LeadResponse(
        lead_id=lead_id,
        name=lead.name,
        contact=lead.contact,
        qualification=qualification,
        created_at=created_at,
    )

    await notify_telegram(response)
    return response


@router.get(
    "/",
    response_model=list[LeadResponse],
    summary="Список всех лидов",
    description="Возвращает историю квалифицированных лидов, сортировка по убыванию даты.",
)
async def list_leads(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[LeadResponse]:
    return get_all_leads(limit=limit, offset=offset)


@router.get(
    "/{lead_id}",
    response_model=LeadResponse,
    summary="Получить лид по ID",
)
async def get_lead(lead_id: str) -> LeadResponse:
    lead = get_lead_by_id(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Лид не найден")
    return lead
