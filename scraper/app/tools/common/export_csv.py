"""
app/tools/common/export_csv.py — Herramienta para exportar los resultados a archivos JSON/CSV.
ponytail: Guarda los datos recolectados crudos en la carpeta de artefactos de manera simple.
"""
import json
import os
from datetime import datetime
from pathlib import Path
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool

# ponytail: ARTIFACTS_DIR fallback standard
ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/tmp/scr4per_artifacts"))

@register_tool("common.export_csv")
class ExportCSVTool(BaseTool):
    platform = None

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        job_id = ctx.job_id
        results = ctx.previous_results

        # Asegurar directorio de destino
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

        # 1. Guardar JSON completo de resultados
        json_path = ARTIFACTS_DIR / f"job_{job_id}.json"
        # ponytail: Remover claves del grafo y artefactos de los datos crudos para no duplicar espacio
        raw_to_save = {k: v for k, v in results.items() if k not in ("graph", "artifacts")}
        json_path.write_text(json.dumps(raw_to_save, ensure_ascii=False, default=str))

        # 2. Guardar JSON del grafo (si está construido)
        graph = results.get("graph")
        graph_path = None
        if graph:
            graph_path = ARTIFACTS_DIR / f"job_{job_id}_graph.json"
            graph_path.write_text(json.dumps(graph, ensure_ascii=False, default=str))

        # Registrar artefactos en el contexto
        artifacts = [
            {"name": json_path.name, "path": str(json_path), "type": "json"}
        ]
        if graph_path:
            artifacts.append({"name": graph_path.name, "path": str(graph_path), "type": "json"})

        ctx.previous_results["artifacts"].extend(artifacts)

        return ToolResult(
            tool_name=self.name,
            status="ok",
            artifacts=artifacts,
            started_at=started,
            finished_at=datetime.now()
        )
