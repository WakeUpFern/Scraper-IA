"""
app/tools/instagram/fetch_followers.py — Extrae lista de seguidores de Instagram.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.instagram.adapter import scrap_list

@register_tool("instagram.fetch_followers")
class InstagramFetchFollowersTool(BaseTool):
    platform = "instagram"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        limit = ctx.limits.get("max_followers", 0)
        profile_data = ctx.previous_results.get("profile") or {}
        username = profile_data.get("username", "unknown")
        
        data = await scrap_list(ctx.page, ctx.target_url, "followers", username, limit)
        ctx.previous_results["followers"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            relationships=data,
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
