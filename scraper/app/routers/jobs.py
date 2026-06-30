"""
app/routers/jobs.py
POST   /v1/jobs                     — crear job (202)
GET    /v1/jobs/{job_id}            — estado, progreso y resumen
POST   /v1/jobs/{job_id}/cancel     — cancelación cooperativa
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.db import get_pool
from app.schemas import JobCreated, JobLimits, JobProgress, JobRequest, JobScope, JobStatus
from app.worker import run_job

logger = logging.getLogger("scr4per.jobs")
router = APIRouter(prefix="/v1/jobs", tags=["jobs"])

# ponytail: track active tasks for cooperative cancel
_active_tasks: dict[int, asyncio.Task] = {}


@router.post("", status_code=202, response_model=JobCreated)
async def create_job(req: JobRequest, background_tasks: BackgroundTasks):
    pool = await get_pool()

    # Supported platforms: facebook, instagram, x
    if req.target.platform not in ("facebook", "instagram", "x"):
        raise HTTPException(422, f"Plataforma '{req.target.platform}' no implementada")

    row = await pool.fetchrow(
        """
        INSERT INTO redes.analisis (tipo_analisis, estado, parametros)
        VALUES ($1, 'queued', $2)
        RETURNING id_analisis, fecha_inicio
        """,
        f"osint_{req.target.platform}",
        json.dumps(req.model_dump(mode="json")),
    )
    job_id: int = row["id_analisis"]
    created_at: datetime = row["fecha_inicio"]

    # Launch background task
    task = asyncio.create_task(run_job(job_id, req))
    _active_tasks[job_id] = task
    task.add_done_callback(lambda _: _active_tasks.pop(job_id, None))

    logger.info("Job %s creado para %s/%s", job_id, req.target.platform, req.target.url_or_username)
    return JobCreated(
        job_id=str(job_id),
        status="queued",
        created_at=created_at,
    )


@router.get("/{job_id}", response_model=JobStatus)
async def get_job(job_id: int):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT * FROM redes.analisis WHERE id_analisis = $1", job_id
    )
    if not row:
        raise HTTPException(404, f"Job {job_id} no encontrado")

    params = row["parametros"] or {}
    if isinstance(params, str):
        try:
            params = json.loads(params)
        except Exception:
            params = {}
    elif not isinstance(params, dict):
        params = {}

    resultado = row["resultado"] or {}
    if isinstance(resultado, str):
        try:
            resultado = json.loads(resultado)
        except Exception:
            resultado = {}
    elif not isinstance(resultado, dict):
        resultado = {}

    target_str = (params.get("target") or {}).get("url_or_username", "?") if isinstance(params, dict) else "?"
    platform_str = (params.get("target") or {}).get("platform", "unknown") if isinstance(params, dict) else "unknown"

    return JobStatus(
        job_id=str(job_id),
        status=row["estado"],
        platform=platform_str,
        target=target_str,
        created_at=row["fecha_inicio"],
        started_at=row["fecha_inicio"] if row["estado"] != "queued" else None,
        finished_at=row["fecha_fin"],
        summary=resultado if resultado else None,
        error=row["error"],
    )


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(job_id: int):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT estado FROM redes.analisis WHERE id_analisis = $1", job_id
    )
    if not row:
        raise HTTPException(404, f"Job {job_id} no encontrado")
    if row["estado"] in ("completed", "failed", "cancelled"):
        return {"job_id": str(job_id), "status": row["estado"], "message": "No cancelable"}

    task = _active_tasks.get(job_id)
    if task and not task.done():
        task.cancel()

    await pool.execute(
        "UPDATE redes.analisis SET estado = 'cancelled', fecha_modificacion = NOW() WHERE id_analisis = $1",
        job_id,
    )
    return {"job_id": str(job_id), "status": "cancelled", "message": "Cancelación solicitada"}
