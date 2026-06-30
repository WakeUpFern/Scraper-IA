"""
app/tools/registry.py — Registro global de herramientas.
ponytail: Decorador simple para registrar clases de herramientas y evitar mapas manuales extensos.
"""
from typing import Dict, Type
from .base import BaseTool

TOOL_REGISTRY: Dict[str, Type[BaseTool]] = {}

def register_tool(name: str):
    def decorator(cls: Type[BaseTool]):
        cls.name = name
        TOOL_REGISTRY[name] = cls
        return cls
    return decorator
