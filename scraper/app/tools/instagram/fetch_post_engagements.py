"""
app/tools/instagram/fetch_post_engagements.py — Extrae likes y comentarios de publicaciones en Instagram.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.instagram.adapter import scrap_post_engagements

@register_tool("instagram.fetch_post_engagements")
class InstagramFetchPostEngagementsTool(BaseTool):
    platform = "instagram"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        max_posts = ctx.limits.get("max_photos", 5)
        profile_data = ctx.previous_results.get("profile") or {}
        username = profile_data.get("username", "unknown")
        
        engagements = await scrap_post_engagements(ctx.page, ctx.target_url, username, max_posts=max_posts)
        
        reactions = engagements.get("reactions", [])
        comments = engagements.get("comments", [])
        
        ctx.previous_results["reactions"] = reactions
        ctx.previous_results["comments"] = comments
        
        return ToolResult(
            tool_name=self.name,
            status="ok",
            reactions=reactions,
            comments=comments,
            raw=engagements,
            started_at=started,
            finished_at=datetime.now()
        )
