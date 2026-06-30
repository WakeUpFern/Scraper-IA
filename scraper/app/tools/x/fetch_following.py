"""
app/tools/x/fetch_following.py — Extrae lista de cuentas seguidas en X.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.x.adapter import scrap_list

@register_tool("x.fetch_following")
class XFetchFollowingTool(BaseTool):
    platform = "x"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        limit = ctx.limits.get("max_following", 0)
        data = await scrap_list(ctx.page, ctx.target_url, "following", limit)
        ctx.previous_results["followed"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            relationships=data,
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
