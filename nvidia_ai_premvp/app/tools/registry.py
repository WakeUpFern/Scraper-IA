"""
Registro central de herramientas (Tool Registry) para Scr4per v3.
Permite registrar y obtener instancias de herramientas disponibles.
"""

from typing import Dict, List, Any
from app.tools.base import BaseTool

_registry: Dict[str, BaseTool] = {}


def register_tool(tool: BaseTool) -> None:
    """Registra una nueva herramienta."""
    _registry[tool.name] = tool


def get_tool(name: str) -> BaseTool | None:
    """Recupera una herramienta por su nombre."""
    return _registry.get(name)


def list_tools() -> List[BaseTool]:
    """Lista todas las herramientas registradas."""
    return list(_registry.values())


def get_tools_definition_for_agent() -> List[Dict[str, Any]]:
    """
    Exporta la definición de las herramientas en formato JSON Schema
    para que la IA interna (planner) conozca las capacidades del microservicio.
    """
    defs = []
    for tool in list_tools():
        defs.append({
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.input_model.model_json_schema()
        })
    return defs


def get_tools_for_openai() -> List[Dict[str, Any]]:
    """
    Exporta las herramientas de adquisición en formato compatible con OpenAI (tools parameter).
    ponytail: omitir herramientas de cierre (grafo/resumen) para que el agente no las llame.
    """
    openai_tools = []
    for tool in list_tools():
        if tool.name in ["build_graph_from_analysis", "summarize_scraping_analysis"]:
            continue
        schema = tool.input_model.model_json_schema()
        schema.pop("title", None)
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": schema
            }
        })
    return openai_tools
