import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import leads, health
from app.services.storage import init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting AI Lead Qualifier API")
    init_db()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="AI Lead Qualifier API",
    description=(
        "Сервис квалификации входящих лидов с помощью ИИ.\n\n"
        "Анализирует описание задачи и выдаёт скор, статус (hot/warm/cold/unqualified) "
        "и рекомендацию — за секунды."
    ),
    version="1.0.0",
    contact={
        "name": "Kirill Tomenko",
        "url": "https://github.com/KirillTomenko",
    },
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(leads.router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )
