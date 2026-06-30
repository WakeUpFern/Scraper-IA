"""
app/tools/facebook/fetch_photo_engagements.py — Extrae reacciones y comentarios de fotos en Facebook.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.facebook.adapter import scrap_photo_engagements

@register_tool("facebook.fetch_photo_engagements")
class FacebookFetchPhotoEngagementsTool(BaseTool):
    platform = "facebook"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        max_photos = ctx.limits.get("max_photos", 5)
        engagements = await scrap_photo_engagements(ctx.page, ctx.target_url, max_photos=max_photos)
        
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
