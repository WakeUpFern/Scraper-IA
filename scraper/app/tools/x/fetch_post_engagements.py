"""
app/tools/x/fetch_post_engagements.py — Extrae comentadores de publicaciones en X.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.x.adapter import scrap_commenters

@register_tool("x.fetch_post_engagements")
class XFetchPostEngagementsTool(BaseTool):
    platform = "x"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        max_posts = ctx.limits.get("max_photos", 10)
        commenters = await scrap_commenters(ctx.page, ctx.target_url, max_posts=max_posts)
        ctx.previous_results["comments"] = commenters
        return ToolResult(
            tool_name=self.name,
            status="ok",
            comments=commenters,
            raw=commenters,
            started_at=started,
            finished_at=datetime.now()
        )
