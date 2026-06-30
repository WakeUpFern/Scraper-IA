"""
app/tools/x/validate_session.py — Valida la sesión activa de X.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.x.adapter import validate_session

@register_tool("x.validate_session")
class XValidateSessionTool(BaseTool):
    platform = "x"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        ok = await validate_session(ctx.page)
        if not ok:
            raise RuntimeError("Sesión de X inválida o expirada")
        return ToolResult(
            tool_name=self.name,
            status="ok",
            started_at=started,
            finished_at=datetime.now()
        )
