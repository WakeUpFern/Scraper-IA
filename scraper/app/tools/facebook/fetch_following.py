"""
app/tools/facebook/fetch_following.py — Extrae lista de cuentas seguidas en Facebook.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.facebook.adapter import scrap_list

@register_tool("facebook.fetch_following")
class FacebookFetchFollowingTool(BaseTool):
    platform = "facebook"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        limit = ctx.limits.get("max_following", 0)
        data = await scrap_list(ctx.page, ctx.target_url, "followed", limit)
        ctx.previous_results["followed"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            relationships=data,
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
