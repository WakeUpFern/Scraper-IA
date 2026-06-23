"""
Paquete de herramientas de Scr4per v3.
Importa y registra las herramientas reales disponibles.
"""

from app.tools.registry import register_tool
from app.tools.resolve_target import ResolveTargetTool
from app.tools.fetch_profile import FetchProfileTool
from app.tools.fetch_followers import FetchFollowersTool
from app.tools.fetch_following import FetchFollowingTool
from app.tools.fetch_posts import FetchRecentPostsTool
from app.tools.fetch_comments import FetchCommentsTool
from app.tools.build_graph import BuildGraphTool
from app.tools.summarize import SummarizeTool

# Registrar todas las herramientas reales en el registry central
register_tool(ResolveTargetTool())
register_tool(FetchProfileTool())
register_tool(FetchFollowersTool())
register_tool(FetchFollowingTool())
register_tool(FetchRecentPostsTool())
register_tool(FetchCommentsTool())
register_tool(BuildGraphTool())
register_tool(SummarizeTool())
