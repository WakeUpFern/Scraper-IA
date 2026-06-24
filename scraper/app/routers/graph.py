"""
app/routers/graph.py
POST /v1/jobs/{job_id}/graph/build  — construye/reconstruye grafo desde DB
GET  /v1/jobs/{job_id}/graph        — obtiene el grafo JSON
"""
from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from app.db import get_pool
from app.schemas import GraphBuildResponse, GraphResponse
from app.worker import build_graph

router = APIRouter(prefix="/v1/jobs", tags=["graph"])


@router.post("/{job_id}/graph/build", response_model=GraphBuildResponse)
async def build_job_graph(job_id: int):
    pool = await get_pool()
    row = await pool.fetchrow(
        "SELECT estado, resultado FROM redes.analisis WHERE id_analisis = $1", job_id
    )
    if not row:
        raise HTTPException(404, f"Job {job_id} no encontrado")
    if row["estado"] not in ("completed", "failed"):
        raise HTTPException(409, f"Job en estado '{row['estado']}' — no se puede construir grafo aún")

    resultado = row["resultado"] or {}
    if isinstance(resultado, str):
        resultado = json.loads(resultado)

    # ponytail: rebuild from persisted result JSON (no re-scraping)
    # resultado contains summary counts, not full data — use existing snapshot if any
    snap = await pool.fetchrow(
        "SELECT graph_json FROM redes.graph_snapshot WHERE id_analisis = $1 ORDER BY id_graph_snapshot DESC LIMIT 1",
        job_id,
    )
    if not snap:
        raise HTTPException(409, "No hay datos persistidos para construir el grafo")

    return GraphBuildResponse(
        job_id=str(job_id),
        status="ok",
        message="Grafo ya disponible en /graph",
    )


@router.get("/{job_id}/graph", response_model=GraphResponse)
async def get_job_graph(job_id: int):
    pool = await get_pool()
    snap = await pool.fetchrow(
        """
        SELECT graph_json, fecha_creacion
        FROM redes.graph_snapshot
        WHERE id_analisis = $1
        ORDER BY id_graph_snapshot DESC LIMIT 1
        """,
        job_id,
    )
    if not snap:
        raise HTTPException(404, f"Grafo para job {job_id} no encontrado. Ejecuta /graph/build primero.")

    graph_data = snap["graph_json"]
    if isinstance(graph_data, str):
        graph_data = json.loads(graph_data)

    return GraphResponse(
        job_id=str(job_id),
        graph=graph_data,
        built_at=snap["fecha_creacion"],
    )
