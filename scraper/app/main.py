"""
app/main.py — Fábrica FastAPI: monta routers, lifespan (DB pool).
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

import logging
from app.db import close_pool
from app.routers import health, jobs, graph, tool_runs, artifacts

# Configurar logging para que los logs del scraper y worker vayan a stdout/stderr y Docker los capture
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ponytail: lazy pool — no falla si la DB no está lista exactamente al inicio
    yield
    await close_pool()


app = FastAPI(
    title="Scr4per MVP",
    version="0.1.0",
    description="Microservicio de adquisición OSINT social — MVP",
    lifespan=lifespan,
)

app.include_router(health.router)
app.include_router(jobs.router)
app.include_router(graph.router)
app.include_router(tool_runs.router)
app.include_router(artifacts.router)
