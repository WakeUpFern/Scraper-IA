"""Rutas internas del worker. La API es dueña del estado y de la persistencia."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.schemas import JobCreated, JobRequest
from app.security import require_service_key
from app.worker import run_job

logger = logging.getLogger("scr4per.jobs")
router = APIRouter(prefix="/internal/v1/jobs", tags=["jobs"], dependencies=[require_service_key])

_active_tasks: dict[int, asyncio.Task] = {}


@router.post("", status_code=202, response_model=JobCreated)
async def create_job(req: JobRequest):
    existing = _active_tasks.get(req.analysis_id)
    if existing and not existing.done():
        return JobCreated(job_id=str(req.analysis_id), status="running", created_at=datetime.now(timezone.utc))

    task = asyncio.create_task(run_job(req.analysis_id, req))
    _active_tasks[req.analysis_id] = task
    task.add_done_callback(lambda _: _active_tasks.pop(req.analysis_id, None))
    logger.info("Job %s aceptado para %s/%s", req.analysis_id, req.target.platform, req.target.url_or_username)
    return JobCreated(job_id=str(req.analysis_id), status="queued", created_at=datetime.now(timezone.utc))


@router.post("/{job_id}/cancel", response_model=dict)
async def cancel_job(job_id: int):
    task = _active_tasks.get(job_id)
    if not task or task.done():
        raise HTTPException(404, f"Job {job_id} no está activo en este worker")
    task.cancel()
    return {"job_id": str(job_id), "status": "cancelled", "message": "Cancelación solicitada"}
