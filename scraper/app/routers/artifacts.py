"""
app/routers/artifacts.py
GET /v1/jobs/{job_id}/artifacts — lista JSON, CSV y otros archivos generados
"""
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.db import get_pool
from app.schemas import ArtifactItem, ArtifactsResponse

router = APIRouter(prefix="/v1/jobs", tags=["artifacts"])

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/tmp/scr4per_artifacts"))


@router.get("/{job_id}/artifacts", response_model=ArtifactsResponse)
async def get_artifacts(job_id: int):
    pool = await get_pool()
    exists = await pool.fetchval(
        "SELECT 1 FROM redes.analisis WHERE id_analisis = $1", job_id
    )
    if not exists:
        raise HTTPException(404, f"Job {job_id} no encontrado")

    items: list[ArtifactItem] = []
    if ARTIFACTS_DIR.exists():
        for p in ARTIFACTS_DIR.iterdir():
            if p.name.startswith(f"job_{job_id}"):
                ext = p.suffix.lstrip(".")
                ftype = {"json": "json", "csv": "csv", "png": "screenshot", "log": "log"}.get(ext, "file")
                items.append(ArtifactItem(
                    name=p.name,
                    type=ftype,
                    path=str(p),
                    size_bytes=p.stat().st_size,
                ))

    return ArtifactsResponse(job_id=str(job_id), artifacts=items)
