"""
Entrypoint FastAPI — nvidia_ai_premvp.

Pre-MVP: solo health + chat hacia NVIDIA NIM.
Sin DB, Gateway, Auth, Playwright ni Scrapling.
"""

import logging

from fastapi import FastAPI
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from app.api.routes_health import router as health_router
from app.api.routes_chat import router as chat_router
from app.api.routes_scraper import router as scraper_router
from app.nvidia.client import close_client
from app.runtime.browser_pool import close_browser_pool
from app.runtime.db import close_db_pool

# Importar el paquete de herramientas para gatillar el registro automático
import app.tools

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("nvidia_ai_premvp arrancando")
    yield
    logger.info("nvidia_ai_premvp cerrando — liberando cliente httpx, base de datos y navegadores")
    await close_client()
    await close_browser_pool()
    await close_db_pool()




app = FastAPI(
    title="nvidia_ai_premvp",
    description="Pre-MVP: proxy hacia NVIDIA NIM para Scr4per v3 y ejecución de herramientas.",
    version="0.2.0",
    lifespan=lifespan,
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(scraper_router)

