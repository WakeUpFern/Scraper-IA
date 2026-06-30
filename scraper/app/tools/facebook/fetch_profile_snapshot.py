"""
app/tools/facebook/fetch_profile_snapshot.py — Extrae información de perfil básica.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.facebook.adapter import get_profile_data

@register_tool("facebook.fetch_profile_snapshot")
class FacebookFetchProfileSnapshotTool(BaseTool):
    platform = "facebook"

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
