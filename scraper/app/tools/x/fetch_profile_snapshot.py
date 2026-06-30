"""
app/tools/x/fetch_profile_snapshot.py — Extrae información de perfil básica de X.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.x.adapter import get_profile_data

@register_tool("x.fetch_profile_snapshot")
class XFetchProfileSnapshotTool(BaseTool):
    platform = "x"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        data = await get_profile_data(ctx.page, ctx.target_url)
        ctx.previous_results["profile"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            profiles=[data] if data else [],
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
