"""
app/tools/base.py — Clases base para el motor de herramientas del scraper.
ponytail: Contenedores simples de contexto y resultado para evitar boilerplate de mapeo de modelos.
"""
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import BrowserContext, Page

class ToolContext:
    def __init__(
        self,
        job_id: int,
        platform: str,
        target_url: str,
        username: str,
        limits: Dict[str, Any],
        scope: Dict[str, Any],
        browser_context: Optional[BrowserContext] = None,
        page: Optional[Page] = None,
    ):
        self.job_id = job_id
        self.platform = platform
        self.target_url = target_url
        self.username = username
        self.limits = limits
        self.scope = scope
        self.browser_context = browser_context
        self.page = page
        # ponytail: El acumulador central de resultados simplifica compartir datos entre herramientas.
        self.previous_results: Dict[str, Any] = {
            "profile": None,
            "friends": [],
            "followers": [],
            "followed": [],
            "reactions": [],
            "comments": [],
            "graph": None,
            "artifacts": []
        }

class ToolResult:
    def __init__(
        self,
        tool_name: str,
        status: str = "ok",  # ok | failed
        profiles: Optional[List[Dict[str, Any]]] = None,
        relationships: Optional[List[Dict[str, Any]]] = None,
        publications: Optional[List[Dict[str, Any]]] = None,
        comments: Optional[List[Dict[str, Any]]] = None,
        reactions: Optional[List[Dict[str, Any]]] = None,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        raw: Optional[Any] = None,
        error: Optional[str] = None,
        started_at: Optional[datetime] = None,
        finished_at: Optional[datetime] = None,
    ):
        self.tool_name = tool_name
        self.status = status
        self.profiles = profiles or []
        self.relationships = relationships or []
        self.publications = publications or []
        self.comments = comments or []
        self.reactions = reactions or []
        self.artifacts = artifacts or []
        self.raw = raw
        self.error = error
        self.started_at = started_at or datetime.now()
        self.finished_at = finished_at or datetime.now()

class BaseTool:
    name: str
    platform: Optional[str] = None

    async def run(self, ctx: ToolContext) -> ToolResult:
        raise NotImplementedError
