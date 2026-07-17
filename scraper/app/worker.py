"""Worker técnico: scrapea y entrega resultados a la API."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from .api_client import CoreApiClient

logger = logging.getLogger("scr4per.worker")


def get_storage_state_path(platform: str) -> str:
    return os.getenv(
        f"{platform.upper()}_STORAGE_STATE",
        str(Path(__file__).parent.parent / "scrapers" / f"{platform}_storage_state.json"),
    )


def _tool_plan(platform: str, scope: dict) -> list[str]:
    plan: list[str] = [f"{platform}.validate_session"]
    if scope.get("profile", True): plan.append(f"{platform}.fetch_profile_snapshot")
    if platform == "facebook" and scope.get("friends", False): plan.append("facebook.fetch_friends")
    if scope.get("followers", False): plan.append(f"{platform}.fetch_followers")
    if scope.get("following", False): plan.append(f"{platform}.fetch_following")
    if platform == "facebook" and (scope.get("photos") or scope.get("reactions") or scope.get("comments")):
        plan.append("facebook.fetch_photo_engagements")
    elif platform in ("instagram", "x") and (scope.get("photos") or scope.get("reactions") or scope.get("comments")):
        plan.append(f"{platform}.fetch_post_engagements")
    return plan + ["common.build_graph", "common.export_excel", "common.export_csv"]


async def run_job(job_id: int, request) -> None:
    from playwright.async_api import async_playwright
    from app.tools.base import ToolContext
    from app.tools.registry import TOOL_REGISTRY
    import app.tools  # registra herramientas

    core = CoreApiClient()
    tool_runs: list[dict] = []
    ctx = None
    try:
        await core.notify(job_id, {"status": "running", "platform": request.target.platform})
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            try:
                browser_context = await browser.new_context(
                    storage_state=get_storage_state_path(request.target.platform),
                    viewport={"width": 1280, "height": 720},
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
                )
                page = await browser_context.new_page()
                ctx = ToolContext(
                    job_id=job_id,
                    platform=request.target.platform,
                    target_url=request.target.url_or_username,
                    username="",
                    limits=request.limits.model_dump(),
                    scope=request.scope.model_dump(),
                    browser_context=browser_context,
                    page=page,
                )

                for tool_name in _tool_plan(request.target.platform, ctx.scope):
                    tool = TOOL_REGISTRY.get(tool_name)
                    if tool is None:
                        raise RuntimeError(f"Herramienta no registrada: {tool_name}")
                    started = datetime.now(timezone.utc)
                    try:
                        result = await tool().run(ctx)
                        tool_runs.append({
                            "tool_name": tool_name, "platform": request.target.platform,
                            "status": result.status, "error": result.error,
                            "input": {"target": request.target.url_or_username},
                            "output": {"artifacts": result.artifacts},
                            "started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
                            "extractor_strategy": "playwright+scrapling",
                        })
                        if result.status != "ok" and tool_name.endswith(("validate_session", "fetch_profile_snapshot")):
                            raise RuntimeError(result.error or f"Fallo crítico en {tool_name}")
                    except Exception as exc:
                        tool_runs.append({
                            "tool_name": tool_name, "platform": request.target.platform,
                            "status": "failed", "error": str(exc),
                            "input": {"target": request.target.url_or_username}, "output": {},
                            "started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
                            "extractor_strategy": "playwright+scrapling",
                        })
                        raise
            finally:
                await browser.close()

        assert ctx is not None
        uploaded: list[dict] = []
        for artifact in ctx.previous_results.get("artifacts", []):
            uploaded.append(await core.upload_artifact(job_id, artifact))
        ctx.previous_results["artifacts"] = uploaded
        await core.notify(job_id, {
            "status": "completed",
            "platform": request.target.platform,
            "results": ctx.previous_results,
            "graph": ctx.previous_results.get("graph"),
            "tool_runs": tool_runs,
            "artifacts": uploaded,
        })
        logger.info("Job %s completado", job_id)
    except asyncio.CancelledError:
        await core.notify(job_id, {"status": "cancelled", "platform": request.target.platform})
        logger.info("Job %s cancelado", job_id)
        raise
    except Exception as exc:
        logger.exception("Job %s falló", job_id)
        try:
            await core.notify(job_id, {
                "status": "failed", "platform": request.target.platform,
                "error": str(exc), "tool_runs": tool_runs,
            })
        except Exception:
            logger.exception("No se pudo informar a la API el fallo del job %s", job_id)
