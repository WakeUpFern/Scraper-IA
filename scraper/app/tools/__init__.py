"""
app/tools/__init__.py — Punto de entrada del motor de herramientas.
ponytail: Importa todos los módulos de herramientas para disparar el decorador de registro automático.
"""
from .base import BaseTool, ToolContext, ToolResult
from .registry import register_tool, TOOL_REGISTRY

# ponytail: Importación explícita para registrar las herramientas dinámicamente.
from .common import build_graph, export_csv, export_excel
from .facebook import (
    validate_session as fb_val,
    fetch_profile_snapshot as fb_snap,
    fetch_friends as fb_fr,
    fetch_followers as fb_fol,
    fetch_following as fb_following,
    fetch_photo_engagements as fb_eng
)
from .instagram import (
    validate_session as ig_val,
    fetch_profile_snapshot as ig_snap,
    fetch_followers as ig_fol,
    fetch_following as ig_following,
    fetch_post_engagements as ig_eng
)
from .x import (
    validate_session as x_val,
    fetch_profile_snapshot as x_snap,
    fetch_followers as x_fol,
    fetch_following as x_following,
    fetch_post_engagements as x_eng
)
