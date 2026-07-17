"""
app/main.py — Fábrica FastAPI: monta routers, lifespan (DB pool).
"""
from fastapi import FastAPI

import logging
from app.routers import health, jobs

# Configurar logging para que los logs del scraper y worker vayan a stdout/stderr y Docker los capture
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


app = FastAPI(
    title="Scr4per MVP",
    version="0.1.0",
    description="Microservicio de adquisición OSINT social — MVP",
)

app.include_router(health.router)
app.include_router(jobs.router)
