import pytest
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.models.lead import LeadRequest, QualificationResult, LeadStatus


def test_lead_request_valid():
    lead = LeadRequest(
        name="Test Company",
        contact="@test",
        task_description="Нужен Telegram-бот для приёма заявок с уведомлениями",
    )
    assert lead.name == "Test Company"
    assert lead.budget is None


def test_lead_request_full():
    lead = LeadRequest(
        name="ООО Рога",
        contact="test@example.com",
        task_description="Автоматизация документооборота с помощью AI",
        budget="100 000 руб",
        deadline="1 месяц",
    )
    assert lead.budget == "100 000 руб"
    assert lead.deadline == "1 месяц"


def test_qualification_result_scores():
    result = QualificationResult(
        score=85,
        status=LeadStatus.HOT,
        fit_score=9,
        budget_score=8,
        urgency_score=9,
        clarity_score=8,
        summary="Клиент хочет автоматизировать Telegram-воронку",
        recommendation="Написать в течение часа, высокий шанс сделки",
        red_flags=[],
        green_flags=["Чёткое ТЗ", "Адекватный бюджет"],
    )
    assert result.score == 85
    assert result.status == LeadStatus.HOT
    assert len(result.green_flags) == 2


def test_lead_status_values():
    assert LeadStatus.HOT == "hot"
    assert LeadStatus.WARM == "warm"
    assert LeadStatus.COLD == "cold"
    assert LeadStatus.UNQUALIFIED == "unqualified"


def test_lead_request_too_short_task():
    with pytest.raises(Exception):
        LeadRequest(
            name="Test",
            contact="@t",
            task_description="коротко",  # < 10 символов
        )
