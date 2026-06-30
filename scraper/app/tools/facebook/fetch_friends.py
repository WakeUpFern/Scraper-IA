"""
app/tools/facebook/fetch_friends.py — Extrae lista de amigos de Facebook.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool
from scrapers.facebook.adapter import scrap_list

@register_tool("facebook.fetch_friends")
class FacebookFetchFriendsTool(BaseTool):
    platform = "facebook"

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        limit = ctx.limits.get("max_friends", 0)
        data = await scrap_list(ctx.page, ctx.target_url, "friends_all", limit)
        ctx.previous_results["friends"] = data
        return ToolResult(
            tool_name=self.name,
            status="ok",
            relationships=data,
            raw=data,
            started_at=started,
            finished_at=datetime.now()
        )
