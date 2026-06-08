from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LeadStatus(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"


class LeadRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Имя или компания лида")
    contact: str = Field(..., min_length=3, max_length=200, description="Email, Telegram или телефон")
    task_description: str = Field(..., min_length=10, max_length=2000, description="Описание задачи/проекта")
    budget: Optional[str] = Field(None, max_length=100, description="Бюджет (если указан)")
    deadline: Optional[str] = Field(None, max_length=100, description="Срок (если указан)")

    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Иван Петров / ООО Ромашка",
                "contact": "@ivan_petrov",
                "task_description": "Нужен Telegram-бот для автоматизации приёма заявок. "
                                    "Клиенты пишут в бот, данные попадают в таблицу, менеджер получает уведомление.",
                "budget": "50 000 руб",
                "deadline": "2 недели",
            }
        }
    }


class QualificationResult(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Общий скор квалификации 0-100")
    status: LeadStatus = Field(..., description="Статус лида")
    fit_score: int = Field(..., ge=0, le=10, description="Соответствие вашей нише 0-10")
    budget_score: int = Field(..., ge=0, le=10, description="Адекватность бюджета 0-10")
    urgency_score: int = Field(..., ge=0, le=10, description="Срочность/мотивация 0-10")
    clarity_score: int = Field(..., ge=0, le=10, description="Чёткость задачи 0-10")
    summary: str = Field(..., description="Краткое резюме лида")
    recommendation: str = Field(..., description="Рекомендация: что делать с этим лидом")
    red_flags: list[str] = Field(default_factory=list, description="Тревожные сигналы")
    green_flags: list[str] = Field(default_factory=list, description="Позитивные сигналы")


class LeadResponse(BaseModel):
    lead_id: str = Field(..., description="Уникальный ID записи")
    name: str
    contact: str
    qualification: QualificationResult
    created_at: str
