"""
app/routers/tool_runs.py
GET /v1/jobs/{job_id}/tool-runs — historial de ejecuciones técnicas por job
"""
from fastapi import APIRouter, HTTPException
from app.db import get_pool
from app.schemas import ToolRunItem, ToolRunsResponse

router = APIRouter(prefix="/v1/jobs", tags=["tool-runs"])


@router.get("/{job_id}/tool-runs", response_model=ToolRunsResponse)
async def get_tool_runs(job_id: int):
    pool = await get_pool()
    exists = await pool.fetchval(
        "SELECT 1 FROM redes.analisis WHERE id_analisis = $1", job_id
    )
    if not exists:
        raise HTTPException(404, f"Job {job_id} no encontrado")

    rows = await pool.fetch(
        """
        SELECT id_tool_run, tool_name, platform, status, error,
               started_at, finished_at, extractor_strategy
        FROM redes.tool_run
        WHERE id_analisis = $1
        ORDER BY started_at
        """,
        job_id,
    )
    items = [
        ToolRunItem(
            id=r["id_tool_run"],
            tool_name=r["tool_name"],
            platform=r["platform"],
            status=r["status"],
            started_at=r["started_at"],
            finished_at=r["finished_at"],
            error=r["error"],
            extractor_strategy=r["extractor_strategy"],
        )
        for r in rows
    ]
    return ToolRunsResponse(job_id=str(job_id), tool_runs=items)
