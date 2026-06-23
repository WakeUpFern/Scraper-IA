"""
Clase base para las herramientas (tools) de Scr4per v3.
Encapsula la ejecución, auditoría automática en tool_run y el registro de evidencia.
"""

import abc
import json
import logging
import traceback
from datetime import datetime
from typing import Any, Type, Generic, TypeVar
from pydantic import BaseModel

import contextvars
from app.tools import mock_db
from app.runtime import db

current_tool_run = contextvars.ContextVar("current_tool_run", default=None)


logger = logging.getLogger(__name__)

InputT = TypeVar("InputT", bound=BaseModel)
OutputT = TypeVar("OutputT", bound=BaseModel)


class BaseTool(abc.ABC, Generic[InputT, OutputT]):
    """
    Clase base abstracta para todas las herramientas.
    Gestiona automáticamente la auditoría real en redes.tool_run.
    """

    def __init__(self, name: str, description: str, input_model: Type[InputT], output_model: Type[OutputT]):
        self.name = name
        self.description = description
        self.input_model = input_model
        self.output_model = output_model

    @property
    def current_tool_run_id(self) -> int | None:
        """Devuelve el id_tool_run real generado en PostgreSQL para esta ejecución."""
        return current_tool_run.get()

    @abc.abstractmethod
    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: InputT) -> OutputT:
        """Lógica real de la herramienta que debe ser implementada por subclases."""
        pass

    async def run(self, id_analisis: int, id_usuario: int | None, raw_input: dict[str, Any]) -> dict[str, Any]:
        """
        Punto de entrada para ejecutar la herramienta.
        Valida entradas, genera registro tool_run en DB y controla fallos.
        """
        started_at = datetime.now()
        
        # Validar input según el modelo de la herramienta
        try:
            validated_input = self.input_model.model_validate(raw_input)
        except Exception as e:
            logger.error("Error de validación en input de tool=%s: %s", self.name, e)
            
            # Guardamos tool_run fallido de inmediato en la base de datos real
            try:
                await db.execute(
                    """
                    INSERT INTO redes.tool_run 
                    (id_analisis, id_usuario, tool_name, input_json, output_json, status, error, started_at, finished_at, cost_json, created_by_agent)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                    """,
                    id_analisis, id_usuario, self.name, json.dumps(raw_input), json.dumps({}),
                    "failed", f"Validation Error: {str(e)}", started_at, datetime.now(), json.dumps({}), True
                )
            except Exception as db_err:
                logger.error("Error registrando tool_run fallido en DB: %s", db_err)

            return {"status": "failed", "error": f"Validation Error: {str(e)}"}

        # Crear tool_run inicial ("running") en PostgreSQL
        id_tool_run = None
        try:
            row = await db.fetchrow(
                """
                INSERT INTO redes.tool_run 
                (id_analisis, id_usuario, tool_name, input_json, output_json, status, error, started_at, cost_json, created_by_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id_tool_run
                """,
                id_analisis, id_usuario, self.name, json.dumps(validated_input.model_dump()), json.dumps({}),
                "running", None, started_at, json.dumps({}), True
            )
            if row:
                id_tool_run = row["id_tool_run"]
        except Exception as db_err:
            logger.error("Error registrando tool_run inicial en DB: %s. Continuando de forma degradada.", db_err)

        # ponytail: registrar en el mock_db local por compatibilidad de fallback
        mock_tr = mock_db.add_tool_run({
            "id_tool_run": id_tool_run or (len(mock_db.tool_runs) + 1),
            "id_analisis": id_analisis,
            "id_usuario": id_usuario,
            "tool_name": self.name,
            "input_json": validated_input.model_dump(),
            "output_json": {},
            "status": "running",
            "error": None,
            "started_at": started_at.isoformat(),
            "finished_at": None,
            "cost_json": {},
            "created_by_agent": True
        })

        # Establecer el id_tool_run en el contexto local de la tarea async
        token = current_tool_run.set(id_tool_run)
        try:
            # Ejecutar lógica concreta de la herramienta
            # Pasamos id_tool_run en el contexto si la herramienta lo necesita
            result: OutputT = await self._run(id_analisis, id_usuario, validated_input)
            output_dict = result.model_dump()
            
            # Actualizar en la base de datos real
            if id_tool_run:
                try:
                    # Intentar leer estrategia si viene en el output
                    strategy = getattr(result, "extractor_strategy", None)
                    parser_ver = getattr(result, "parser_version", None)
                    await db.execute(
                        """
                        UPDATE redes.tool_run 
                        SET status = $1, output_json = $2, finished_at = $3, extractor_strategy = $4, parser_version = $5
                        WHERE id_tool_run = $6
                        """,
                        "completed", json.dumps(output_dict), datetime.now(), strategy, parser_ver, id_tool_run
                    )
                except Exception as db_err:
                    logger.error("Error actualizando tool_run en DB: %s", db_err)

            # Actualizar mock_db
            mock_tr["status"] = "completed"
            mock_tr["output_json"] = output_dict
            mock_tr["finished_at"] = datetime.now().isoformat()
            
            return output_dict
            
        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            logger.error("Error ejecutando tool=%s: %s\n%s", self.name, err_msg, traceback.format_exc())
            
            # Actualizar en DB real
            if id_tool_run:
                try:
                    await db.execute(
                        """
                        UPDATE redes.tool_run 
                        SET status = $1, error = $2, finished_at = $3
                        WHERE id_tool_run = $4
                        """,
                        "failed", err_msg, datetime.now(), id_tool_run
                    )
                except Exception as db_err:
                    logger.error("Error actualizando tool_run fallido en DB: %s", db_err)

            # Actualizar mock_db
            mock_tr["status"] = "failed"
            mock_tr["error"] = err_msg
            mock_tr["finished_at"] = datetime.now().isoformat()
            
            return {"status": "failed", "error": err_msg}
        finally:
            current_tool_run.reset(token)

    async def save_raw_evidence(
        self, 
        id_analisis: int, 
        id_tool_run: int | None = None, 
        evidence_type: str = "network_capture", 
        platform: str = "instagram", 
        source_url: str | None = None, 
        raw_json: Any = None, 
        metadata: dict[str, Any] | None = None
    ) -> None:

        """
        Guarda la evidencia cruda en la base de datos real redes.raw_evidence.
        """
        if id_tool_run is None:
            id_tool_run = self.current_tool_run_id
        # Registrar en la base de datos real
        try:
            await db.execute(
                """
                INSERT INTO redes.raw_evidence 
                (id_analisis, id_tool_run, evidence_type, platform, source_url, raw_json, metadata, observed_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                id_analisis, id_tool_run, evidence_type, platform, source_url, 
                json.dumps(raw_json), json.dumps(metadata or {}), datetime.now()
            )
        except Exception as db_err:
            logger.error("Error guardando raw_evidence en DB: %s", db_err)

        # ponytail: registrar en el mock_db local
        mock_db.add_raw_evidence({
            "id_analisis": id_analisis,
            "id_tool_run": id_tool_run,
            "evidence_type": evidence_type,
            "platform": platform,
            "source_url": source_url,
            "raw_json": raw_json,
            "metadata": metadata or {}
        })

