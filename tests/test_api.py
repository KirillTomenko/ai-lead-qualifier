import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Подменяем настройки до импорта приложения
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["DB_PATH"] = "/tmp/test_leads.db"

from app.main import app
from app.services.storage import init_db

pytestmark = pytest.mark.asyncio(loop_scope="function")


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    """Инициализируем чистую БД перед каждым тестом."""
    db_file = tmp_path / "leads.db"
    os.environ["DB_PATH"] = str(db_file)
    # Перезагружаем settings и пересоздаём DB_PATH в storage
    import importlib
    import app.config as cfg
    import app.services.storage as storage
    cfg.settings = cfg.Settings()
    storage.DB_PATH = __import__("pathlib").Path(cfg.settings.db_path)
    init_db()
    yield


MOCK_AI_RESPONSE = {
    "score": 82,
    "status": "hot",
    "fit_score": 9,
    "budget_score": 8,
    "urgency_score": 8,
    "clarity_score": 9,
    "summary": "Клиент из e-commerce хочет Telegram-бота для автоматизации заявок.",
    "recommendation": "Написать сегодня, высокий шанс сделки.",
    "red_flags": [],
    "green_flags": ["Чёткое ТЗ", "Адекватный бюджет", "Срочно нужно"],
}


def make_mock_openai_response():
    msg = MagicMock()
    msg.content = json.dumps(MOCK_AI_RESPONSE)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_qualify_lead_success():
    mock_resp = make_mock_openai_response()

    with patch(
        "app.services.qualifier.AsyncOpenAI"
    ) as mock_cls, patch(
        "app.services.notifier.notify_telegram", new_callable=AsyncMock
    ):
        instance = AsyncMock()
        instance.chat.completions.create = AsyncMock(return_value=mock_resp)
        mock_cls.return_value = instance

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.post(
                "/leads/qualify",
                json={
                    "name": "ООО Тест",
                    "contact": "@test_user",
                    "task_description": "Telegram-бот для приёма заявок с уведомлениями в CRM",
                    "budget": "60 000 руб",
                    "deadline": "3 недели",
                },
            )

    assert r.status_code == 201
    data = r.json()
    assert data["qualification"]["score"] == 82
    assert data["qualification"]["status"] == "hot"
    assert data["lead_id"] is not None


@pytest.mark.asyncio
async def test_qualify_lead_missing_fields():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.post("/leads/qualify", json={"name": "Test"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_leads_empty():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/leads/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_get_lead_not_found():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/leads/nonexistent-id")
    assert r.status_code == 404
