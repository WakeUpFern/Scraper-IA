"""
app/worker.py — Background task que ejecuta un job de scraping y persiste resultados en DB.
ponytail: asyncio.create_task, sin Celery, sin Redis.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

from .db import get_pool

if TYPE_CHECKING:
    from .schemas import JobRequest

logger = logging.getLogger("scr4per.worker")

STORAGE_STATE_PATH = os.getenv(
    "FB_STORAGE_STATE",
    str(Path(__file__).parent.parent / "scrapers" / "facebook_storage_state.json"),
)
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/tmp/scr4per_artifacts"))


# ---------------------------------------------------------------------------
# Helpers: persist to redes.analisis + related tables
# ---------------------------------------------------------------------------

async def _update_analisis(pool, job_id: int, **fields):
    """Actualiza columnas en redes.analisis por job_id (=id_analisis)."""
    sets = ", ".join(f"{k} = ${i+2}" for i, k in enumerate(fields))
    vals = list(fields.values())
    await pool.execute(
        f"UPDATE redes.analisis SET {sets}, fecha_modificacion = NOW() WHERE id_analisis = $1",
        job_id, *vals,
    )


async def _insert_tool_run(pool, id_analisis: int, tool_name: str, platform: str,
                            input_data: dict, output_data: dict, status: str,
                            error: str | None, started: datetime, finished: datetime,
                            strategy: str | None = None) -> int:
    row = await pool.fetchrow(
        """
        INSERT INTO redes.tool_run
            (id_analisis, tool_name, platform, input_json, output_json,
             status, error, started_at, finished_at, extractor_strategy)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
        RETURNING id_tool_run
        """,
        id_analisis, tool_name, platform,
        json.dumps(input_data), json.dumps(output_data),
        status, error, started, finished, strategy,
    )
    return row["id_tool_run"]


async def _save_graph_snapshot(pool, id_analisis: int, graph: dict) -> None:
    await pool.execute(
        """
        INSERT INTO redes.graph_snapshot (id_analisis, graph_scope, graph_json, metrics_json)
        VALUES ($1, 'job', $2, $3)
        """,
        id_analisis,
        json.dumps(graph),
        json.dumps({"nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", []))}),
    )


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_graph(results: dict, job_id: int) -> dict:
    """Construye un grafo técnico mínimo desde los resultados del scraper."""
    nodes = {}
    edges = []

    def _node(user: dict, role: str = "contact") -> str:
        key = user.get("link_usuario", user.get("username_usuario", "?"))
        if key not in nodes:
            nodes[key] = {
                "id": key,
                "platform": "facebook",
                "username": user.get("username_usuario"),
                "nombre": user.get("nombre_usuario"),
                "foto": user.get("foto_usuario"),
                "role": role,
            }
        return key

    profile = results.get("profile")
    if profile:
        center = profile.get("url_usuario", profile.get("username", "target"))
        nodes[center] = {
            "id": center,
            "platform": "facebook",
            "username": profile.get("username"),
            "nombre": profile.get("nombre_completo"),
            "foto": profile.get("foto_perfil"),
            "role": "target",
        }

        for u in results.get("friends", []):
            nid = _node(u)
            edges.append({"src": center, "dst": nid, "type": "FRIEND", "job": job_id})

        for u in results.get("followers", []):
            nid = _node(u)
            edges.append({"src": nid, "dst": center, "type": "FOLLOWER", "job": job_id})

        for u in results.get("followed", []):
            nid = _node(u)
            edges.append({"src": center, "dst": nid, "type": "FOLLOWING", "job": job_id})

        for u in results.get("reactions", []):
            nid = _node(u)
            edges.append({"src": nid, "dst": center, "type": "REACTED", "job": job_id})

        for u in results.get("comments", []):
            nid = _node(u)
            edges.append({"src": nid, "dst": center, "type": "COMMENTED", "job": job_id})

    return {"nodes": list(nodes.values()), "edges": edges}


# ---------------------------------------------------------------------------
# Main worker
# ---------------------------------------------------------------------------

async def run_job(job_id: int, request: "JobRequest") -> None:
    """
    Ejecuta el análisis completo:
    1. running → scraping → persisting → graph_building → completed/failed
    """
    pool = await get_pool()
    started = datetime.now()  # Usar naive datetime para evitar incompatibilidad con 'timestamp without time zone' en DB

    await _update_analisis(pool, job_id, estado="running", fecha_inicio=started)
    logger.info("[job %s] Iniciando scraping de %s...", job_id, request.target.url_or_username)

    results: dict = {}
    tool_error: str | None = None
    tool_started = datetime.now()

    try:
        if request.target.platform == "facebook":
            import sys, pathlib
            # ponytail: ensure /app is in path when imported via app.main
            _root = str(pathlib.Path(__file__).parent.parent)
            if _root not in sys.path:
                sys.path.insert(0, _root)
            from scrapers.facebook.adapter import run_analysis

            progress_steps: list = []

            def on_progress(step: str, data: dict):
                progress_steps.append({"step": step, "data": data, "ts": datetime.now(timezone.utc).isoformat()})

            results = await run_analysis(
                profile_url=request.target.url_or_username,
                storage_state_path=STORAGE_STATE_PATH,
                scope=request.scope.model_dump(),
                limits=request.limits.model_dump(),
                headless=True,
                on_progress=on_progress,
            )
        else:
            raise NotImplementedError(f"Plataforma '{request.target.platform}' no implementada aún")

    except Exception as exc:
        tool_error = str(exc)
        logger.error("[job %s] Error en scraping: %s", job_id, exc)

    tool_finished = datetime.now()

    # Persist tool_run record
    await _insert_tool_run(
        pool,
        id_analisis=job_id,
        tool_name="run_analysis",
        platform=request.target.platform,
        input_data=request.model_dump(mode="json"),
        output_data={
            "profile": results.get("profile"),
            "counts": {
                "friends": len(results.get("friends", [])),
                "followers": len(results.get("followers", [])),
                "followed": len(results.get("followed", [])),
                "reactions": len(results.get("reactions", [])),
                "comments": len(results.get("comments", [])),
            },
        },
        status="failed" if tool_error else "ok",
        error=tool_error,
        started=tool_started,
        finished=tool_finished,
        strategy="playwright+scrapling",
    )

    if tool_error:
        await _update_analisis(
            pool, job_id,
            estado="failed",
            error=tool_error,
            fecha_fin=tool_finished,
            resultado=json.dumps({}),
        )
        return

    # --- persisting ---
    await _update_analisis(pool, job_id, estado="persisting")

    # Save CSV artifact
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = ARTIFACTS_DIR / f"job_{job_id}.json"
    csv_path.write_text(json.dumps(results, ensure_ascii=False, default=str))

    # --- graph_building ---
    await _update_analisis(pool, job_id, estado="graph_building")
    graph = build_graph(results, job_id)
    await _save_graph_snapshot(pool, job_id, graph)

    graph_path = ARTIFACTS_DIR / f"job_{job_id}_graph.json"
    graph_path.write_text(json.dumps(graph, ensure_ascii=False, default=str))

    summary = {
        "profile": results.get("profile", {}).get("nombre_completo"),
        "friends": len(results.get("friends", [])),
        "followers": len(results.get("followers", [])),
        "followed": len(results.get("followed", [])),
        "reactions": len(results.get("reactions", [])),
        "comments": len(results.get("comments", [])),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
    }

    await _update_analisis(
        pool, job_id,
        estado="completed",
        resultado=json.dumps(summary),
        fecha_fin=datetime.now(),
    )
    logger.info("[job %s] Completado. %s", job_id, summary)
