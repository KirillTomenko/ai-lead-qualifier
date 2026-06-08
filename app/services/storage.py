import sqlite3
import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from app.models.lead import LeadResponse, QualificationResult, LeadStatus
from app.config import settings

logger = logging.getLogger(__name__)

DB_PATH = Path(settings.db_path)


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    """Контекстный менеджер: соединение всегда корректно закрывается."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    """Создаёт таблицу leads при первом запуске."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS leads (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                contact     TEXT NOT NULL,
                task        TEXT NOT NULL,
                budget      TEXT,
                deadline    TEXT,
                score       INTEGER NOT NULL,
                status      TEXT NOT NULL,
                result_json TEXT NOT NULL,
                created_at  TEXT NOT NULL
            )
            """
        )
        conn.commit()
    logger.info("DB initialized at %s", DB_PATH)


def save_lead(lead_id: str, name: str, contact: str, task: str,
              budget: str | None, deadline: str | None,
              result: QualificationResult) -> str:
    """Сохраняет лид и результат квалификации. Возвращает created_at."""
    created_at = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO leads
                (id, name, contact, task, budget, deadline, score, status, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                name,
                contact,
                task,
                budget,
                deadline,
                result.score,
                result.status.value,
                result.model_dump_json(),
                created_at,
            ),
        )
        conn.commit()
    return created_at


def get_lead_by_id(lead_id: str) -> LeadResponse | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM leads WHERE id = ?", (lead_id,)
        ).fetchone()

    if not row:
        return None
    return _row_to_response(row)


def get_all_leads(limit: int = 50, offset: int = 0) -> list[LeadResponse]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [_row_to_response(r) for r in rows]


def _row_to_response(row: sqlite3.Row) -> LeadResponse:
    result_data = json.loads(row["result_json"])
    return LeadResponse(
        lead_id=row["id"],
        name=row["name"],
        contact=row["contact"],
        qualification=QualificationResult(**result_data),
        created_at=row["created_at"],
    )
