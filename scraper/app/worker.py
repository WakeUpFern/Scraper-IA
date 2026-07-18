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

def get_storage_state_path(platform: str) -> str:
    env_var = f"{platform.upper()}_STORAGE_STATE"
    default_name = f"{platform}_storage_state.json"
    return os.getenv(
        env_var,
        str(Path(__file__).parent.parent / "scrapers" / default_name),
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

def build_graph(results: dict, job_id: int, platform: str) -> dict:
    """Construye un grafo técnico mínimo desde los resultados del scraper."""
    nodes = {}
    edges = []

    def _node(user: dict, role: str = "contact") -> str:
        key = user.get("link_usuario", user.get("username_usuario", "?"))
        if key not in nodes:
            nodes[key] = {
                "id": key,
                "platform": platform,
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
            "platform": platform,
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
    Ejecuta el análisis completo usando el motor de herramientas modular.
    """
    from playwright.async_api import async_playwright
    from app.tools.base import ToolContext
    from app.tools.registry import TOOL_REGISTRY
    import app.tools  # Trigger registrations

    pool = await get_pool()
    started = datetime.now()

    try:
        await _update_analisis(pool, job_id, estado="running", fecha_inicio=started)
        logger.info("[job %s] Iniciando ejecución modular de %s...", job_id, request.target.url_or_username)

        platform = request.target.platform
        scope = request.scope.model_dump()
        limits = request.limits.model_dump()

        # ponytail: Determinar dinámicamente el plan de herramientas
        plan = []
        if platform == "facebook":
            plan.append("facebook.validate_session")
            if scope.get("profile", True):
                plan.append("facebook.fetch_profile_snapshot")
            if scope.get("friends", False):
                plan.append("facebook.fetch_friends")
            if scope.get("followers", False):
                plan.append("facebook.fetch_followers")
            if scope.get("following", False):
                plan.append("facebook.fetch_following")
            if scope.get("photos", False) or scope.get("reactions", False) or scope.get("comments", False):
                plan.append("facebook.fetch_photo_engagements")
        elif platform == "instagram":
            plan.append("instagram.validate_session")
            if scope.get("profile", True):
                plan.append("instagram.fetch_profile_snapshot")
            if scope.get("followers", False):
                plan.append("instagram.fetch_followers")
            if scope.get("following", False):
                plan.append("instagram.fetch_following")
            if scope.get("photos", False) or scope.get("reactions", False) or scope.get("comments", False):
                plan.append("instagram.fetch_post_engagements")
        elif platform == "x":
            plan.append("x.validate_session")
            if scope.get("profile", True):
                plan.append("x.fetch_profile_snapshot")
            if scope.get("followers", False):
                plan.append("x.fetch_followers")
            if scope.get("following", False):
                plan.append("x.fetch_following")
            if scope.get("comments", False):
                plan.append("x.fetch_post_engagements")

        # Agregar herramientas comunes
        plan.append("common.build_graph")
        plan.append("common.persist_results")
        plan.append("common.export_excel")
        plan.append("common.export_csv")

        logger.info("[job %s] Plan de herramientas: %s", job_id, plan)

        storage_state = get_storage_state_path(platform)
        
        async with async_playwright() as pw:
            # ponytail: Navegador centralizado
            browser = await pw.chromium.launch(
                headless=True,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                ],
            )
            browser_context = await browser.new_context(
                storage_state=storage_state,
                viewport={"width": 1280, "height": 720},
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
            )
            page = await browser_context.new_page()

            ctx = ToolContext(
                job_id=job_id,
                platform=platform,
                target_url=request.target.url_or_username,
                username="",
                limits=limits,
                scope=scope,
                browser_context=browser_context,
                page=page,
                db_pool=pool,
            )

            job_failed = False
            job_error_msg = None

            for tool_name in plan:
                if tool_name not in TOOL_REGISTRY:
                    logger.error("[job %s] Herramienta %s no registrada", job_id, tool_name)
                    continue

                tool_cls = TOOL_REGISTRY[tool_name]
                tool_inst = tool_cls()
                tool_started = datetime.now()

                logger.info("[job %s] Ejecutando %s...", job_id, tool_name)
                try:
                    if job_failed and not tool_name.startswith("common."):
                        logger.warning("[job %s] Omitiendo %s por fallo crítico previo", job_id, tool_name)
                        continue

                    res = await tool_inst.run(ctx)
                    tool_finished = datetime.now()

                    # Guardar en redes.tool_run
                    await _insert_tool_run(
                        pool,
                        id_analisis=job_id,
                        tool_name=tool_name,
                        platform=platform,
                        input_data={"target": request.target.url_or_username},
                        output_data={"status": res.status, "artifacts": res.artifacts},
                        status=res.status,
                        error=res.error,
                        started=tool_started,
                        finished=tool_finished,
                        strategy="playwright+scrapling"
                    )

                except Exception as exc:
                    tool_finished = datetime.now()
                    err_str = str(exc)
                    logger.error("[job %s] Error en %s: %s", job_id, tool_name, err_str)

                    await _insert_tool_run(
                        pool,
                        id_analisis=job_id,
                        tool_name=tool_name,
                        platform=platform,
                        input_data={"target": request.target.url_or_username},
                        output_data={"status": "failed"},
                        status="failed",
                        error=err_str,
                        started=tool_started,
                        finished=tool_finished,
                        strategy="playwright+scrapling"
                    )

                    is_critical = tool_name.endswith(".validate_session") or tool_name.endswith(".fetch_profile_snapshot")
                    if is_critical:
                        job_failed = True
                        job_error_msg = err_str
                        break
                    else:
                        if "errors" not in ctx.previous_results:
                            ctx.previous_results["errors"] = []
                        ctx.previous_results["errors"].append({"tool": tool_name, "error": err_str})

            await browser.close()

        if job_failed:
            await _update_analisis(
                pool, job_id,
                estado="failed",
                error=job_error_msg,
                fecha_fin=datetime.now(),
                resultado=json.dumps({"error": job_error_msg}),
            )
            logger.error("[job %s] Job fallido. Error crítico: %s", job_id, job_error_msg)
            return

        # Guardar snapshot del grafo si build_graph funcionó
        graph = ctx.previous_results.get("graph")
        if graph:
            await _update_analisis(pool, job_id, estado="graph_building")
            await _save_graph_snapshot(pool, job_id, graph)

        results = ctx.previous_results
        summary = {
            "profile": results.get("profile", {}).get("nombre_completo") if results.get("profile") else request.target.url_or_username,
            "friends": len(results.get("friends", [])),
            "followers": len(results.get("followers", [])),
            "followed": len(results.get("followed", [])),
            "reactions": len(results.get("reactions", [])),
            "comments": len(results.get("comments", [])),
            "nodes": len(graph["nodes"]) if graph else 0,
            "edges": len(graph["edges"]) if graph else 0,
            "artifacts_count": len(results.get("artifacts", [])),
            "errors": results.get("errors", [])
        }

        await _update_analisis(
            pool, job_id,
            estado="completed",
            resultado=json.dumps(summary),
            fecha_fin=datetime.now(),
        )
        logger.info("[job %s] Completado. %s", job_id, summary)

    except Exception as exc:
        logger.exception("[job %s] Error catastrófico en run_job: %s", job_id, exc)
        try:
            await _update_analisis(
                pool, job_id,
                estado="failed",
                error=str(exc),
                fecha_fin=datetime.now(),
                resultado=json.dumps({"error": str(exc)}),
            )
        except Exception as db_exc:
            logger.error("[job %s] No se pudo guardar el error en base de datos: %s", job_id, db_exc)
