"""
app/routers/health.py
GET /health/live  — proceso activo
GET /health/ready — DB + dependencias
"""
from fastapi import APIRouter
from app.db import get_pool

router = APIRouter(tags=["health"])


@router.get("/health/live")
async def live():
    return {"status": "ok"}


@router.get("/health/ready")
async def ready():
    try:
        pool = await get_pool()
        await pool.fetchval("SELECT 1")
        db = "ok"
    except Exception as exc:
        db = f"error: {exc}"

    overall = "ok" if db == "ok" else "degraded"
    return {"status": overall, "checks": {"db": db}}
