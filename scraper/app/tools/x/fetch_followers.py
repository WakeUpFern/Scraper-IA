"""
app/tools/x/fetch_followers.py — Extrae lista de seguidores de X.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.x.adapter import scrap_list

@register_tool("x.fetch_followers")
class XFetchFollowersTool(BaseTool):
    platform = "x"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        limit = ctx.limits.get("max_followers", 0)
        data = await scrap_list(ctx.page, ctx.target_url, "followers", limit)
        ctx.previous_results["followers"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            relationships=data,
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
