"""
app/tools/instagram/validate_session.py — Valida la sesión activa de Instagram.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.instagram.adapter import validate_session

@register_tool("instagram.validate_session")
class InstagramValidateSessionTool(BaseTool):
    platform = "instagram"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        ok = await validate_session(ctx.page)
        if not ok:
            raise RuntimeError("Sesión de Instagram inválida o expirada")
        return ToolResult(
            tool_name=self.name,
            status="ok",
            started_at=started,
            finished_at=datetime.now()
        )
