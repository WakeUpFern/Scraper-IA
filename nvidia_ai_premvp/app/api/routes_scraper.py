"""
Rutas de la API de Scr4per v3 MVP.
Implementa el ciclo de análisis de scraping y ejecución de herramientas con soporte real en PostgreSQL.
"""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.runtime import db
from app.tools import mock_db
from app.tools.registry import get_tool

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["scraper"])


# --- Schemas ---

class ScrapingLimits(BaseModel):
    max_followers: int = Field(default=100)
    max_following: int = Field(default=100)
    max_posts: int = Field(default=10)
    max_comments_per_post: int = Field(default=50)


class StartAnalysisRequest(BaseModel):
    id_usuario: int
    id_caso: Optional[int] = None
    id_identidad_digital_objetivo: Optional[int] = None
    platform: str
    username_or_url: str
    limits: ScrapingLimits = Field(default_factory=ScrapingLimits)


# --- Endpoint 1: Iniciar análisis de scraping ---

async def execute_analysis_workflow(id_analisis: int, request: StartAnalysisRequest):
    """
    Ejecuta el bucle inteligente ReAct guiado por el planificador de IA en segundo plano.
    """
    from app.agent.planner import ScraperAgentPlanner

    # 1. Actualizar estado del análisis a 'en_progreso' en PostgreSQL
    try:
        await db.execute(
            "UPDATE redes.analisis SET estado = 'en_progreso', fecha_inicio = CURRENT_TIMESTAMP WHERE id_analisis = $1",
            id_analisis
        )
    except Exception as db_err:
        logger.error("Error actualizando redes.analisis a en_progreso: %s", db_err)

    # También en el mock_db local para mantener compatibilidad
    mock_db.update_analysis_status(id_analisis, "running")

    try:
        # 2. Inicializar y ejecutar el Agente Planificador ReAct
        planner = ScraperAgentPlanner(
            id_analisis=id_analisis,
            id_usuario=request.id_usuario,
            platform=request.platform,
            username_or_url=request.username_or_url,
            limits=request.limits.model_dump()
        )
        
        # Ejecutar bucle autónomo del agente
        agent_result = await planner.run()
        logger.info("Agente planificador finalizó con estado: %s. Resp: %s", agent_result.get("status"), agent_result.get("final_reply"))

        # 3. Cierre automatizado por el orquestador: Generar grafo y resumen técnico
        logger.info("Orquestador iniciando cierre del análisis (grafo y resumen)...")
        
        # build_graph_from_analysis
        graph_tool = get_tool("build_graph_from_analysis")
        if graph_tool:
            await graph_tool.run(
                id_analisis=id_analisis,
                id_usuario=request.id_usuario,
                raw_input={"id_analisis": id_analisis}
            )

        # summarize_scraping_analysis
        sum_tool = get_tool("summarize_scraping_analysis")
        if sum_tool:
            await sum_tool.run(
                id_analisis=id_analisis,
                id_usuario=request.id_usuario,
                raw_input={"id_analisis": id_analisis}
            )

        # Actualizar a completado en PostgreSQL
        try:
            await db.execute(
                "UPDATE redes.analisis SET estado = 'completado', fecha_fin = CURRENT_TIMESTAMP WHERE id_analisis = $1",
                id_analisis
            )
        except Exception as db_err:
            logger.error("Error actualizando redes.analisis a completado: %s", db_err)

        mock_db.update_analysis_status(id_analisis, "completed")

    except Exception as e:
        logger.error("Fallo durante execute_analysis_workflow para analisis=%d: %s", id_analisis, e)
        try:
            await db.execute(
                "UPDATE redes.analisis SET estado = 'fallido', error = $1, fecha_fin = CURRENT_TIMESTAMP WHERE id_analisis = $2",
                str(e), id_analisis
            )
        except Exception as db_err:
            logger.error("Error actualizando redes.analisis a fallido: %s", db_err)

        mock_db.update_analysis_status(id_analisis, "failed", error=str(e))


@router.post("/analyses/{id_analisis}/run")
async def run_analysis(id_analisis: int, request: StartAnalysisRequest, background_tasks: BackgroundTasks):
    """Inicia el análisis de scraping en segundo plano."""
    # 1. Asegurar o actualizar el análisis en la base de datos real
    try:
        row = await db.fetchrow("SELECT id_analisis FROM redes.analisis WHERE id_analisis = $1", id_analisis)
        params_json = json.dumps({
            "limits": request.limits.model_dump(),
            "target": request.username_or_url,
            "platform": request.platform
        })
        if not row:
            await db.execute(
                """
                INSERT INTO redes.analisis 
                (id_analisis, id_usuario_ejecutor, tipo_analisis, estado, parametros, id_identidad_digital_objetivo)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                id_analisis, request.id_usuario, "social", "pendiente", params_json, request.id_identidad_digital_objetivo
            )
        else:
            await db.execute(
                """
                UPDATE redes.analisis 
                SET estado = 'pendiente', id_usuario_ejecutor = $1, parametros = $2, id_identidad_digital_objetivo = $3
                WHERE id_analisis = $4
                """,
                request.id_usuario, params_json, request.id_identidad_digital_objetivo, id_analisis
            )
            
        # Si se pasa id_caso, asegurar el link en caso_analisis
        if request.id_caso:
            await db.execute(
                """
                INSERT INTO casos.caso_analisis (id_caso, id_analisis)
                VALUES ($1, $2)
                ON CONFLICT (id_caso, id_analisis) DO NOTHING
                """,
                request.id_caso, id_analisis
            )
    except Exception as db_err:
        logger.error("Error inicializando redes.analisis en DB: %s", db_err)

    # 2. Inicializar en mock_db local para compatibilidad
    analysis = mock_db.init_analysis(
        id_analisis=id_analisis,
        id_usuario=request.id_usuario,
        id_caso=request.id_caso,
        platform=request.platform,
        target=request.username_or_url,
        limits=request.limits.model_dump()
    )
    
    background_tasks.add_task(execute_analysis_workflow, id_analisis, request)
    return {"message": "Análisis iniciado correctamente en segundo plano.", "analysis": analysis}


# --- Endpoint 2: Ejecutar herramienta explícita ---

@router.post("/analyses/{id_analisis}/tools/{tool_name}/run")
async def run_explicit_tool(id_analisis: int, tool_name: str, payload: Dict[str, Any], id_usuario: Optional[int] = None):
    """Ejecuta una herramienta de manera explícita (para testing/crawling manual)."""
    tool = get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Herramienta '{tool_name}' no encontrada en el registro.")
    
    result = await tool.run(id_analisis=id_analisis, id_usuario=id_usuario, raw_input=payload)
    if "status" in result and result["status"] == "failed":
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# --- Endpoint 3: Consultar estado del análisis ---

@router.get("/analyses/{id_analisis}/status")
async def get_analysis_status(id_analisis: int):
    """Consulta el progreso y estado actual de un análisis de scraping desde PostgreSQL."""
    row = await db.fetchrow("SELECT * FROM redes.analisis WHERE id_analisis = $1", id_analisis)
    if not row:
        raise HTTPException(status_code=404, detail=f"Análisis {id_analisis} no encontrado.")
    
    # Obtener el caso asociado si existe
    caso_row = await db.fetchrow("SELECT id_caso FROM casos.caso_analisis WHERE id_analisis = $1 LIMIT 1", id_analisis)
    id_caso = caso_row["id_caso"] if caso_row else None
    
    # Extraer parámetros si existen
    params = {}
    if row.get("parametros"):
        try:
            params = json.loads(row["parametros"]) if isinstance(row["parametros"], str) else row["parametros"]
        except Exception:
            pass

    return {
        "id_analisis": row["id_analisis"],
        "id_usuario": row["id_usuario_ejecutor"],
        "id_caso": id_caso,
        "platform": params.get("platform", "social"),
        "username_or_url": params.get("target", ""),
        "limits": params.get("limits", {}),
        "status": row["estado"],
        "started_at": row["fecha_inicio"].isoformat() if row["fecha_inicio"] else None,
        "finished_at": row["fecha_fin"].isoformat() if row["fecha_fin"] else None,
        "error": row["error"]
    }


# --- Endpoint 4: Consultar tool runs ---

@router.get("/analyses/{id_analisis}/tool-runs")
async def get_analysis_tool_runs(id_analisis: int):
    """Devuelve el historial de ejecuciones de herramientas asociadas a un análisis desde PostgreSQL."""
    rows = await db.fetch(
        """
        SELECT id_tool_run, tool_name, status, error, started_at, finished_at, extractor_strategy 
        FROM redes.tool_run 
        WHERE id_analisis = $1 
        ORDER BY id_tool_run ASC
        """,
        id_analisis
    )
    return [
        {
            "id_tool_run": r["id_tool_run"],
            "tool_name": r["tool_name"],
            "status": r["status"],
            "error": r["error"],
            "started_at": r["started_at"].isoformat() if r["started_at"] else None,
            "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None,
            "extractor_strategy": r["extractor_strategy"]
        }
        for r in rows
    ]


# --- Endpoint 5: Generar y obtener grafo ---

@router.post("/analyses/{id_analisis}/graph/build")
async def build_and_get_graph(id_analisis: int, id_usuario: Optional[int] = None):
    """Fuerza la construcción del grafo técnico a partir de las observaciones recolectadas."""
    graph_tool = get_tool("build_graph_from_analysis")
    if not graph_tool:
        raise HTTPException(status_code=500, detail="Herramienta build_graph_from_analysis no disponible.")
    
    result = await graph_tool.run(id_analisis=id_analisis, id_usuario=id_usuario, raw_input={"id_analisis": id_analisis})
    return result
