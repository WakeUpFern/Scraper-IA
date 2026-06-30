"""
app/tools/common/build_graph.py — Herramienta para construir el grafo técnico.
ponytail: Reutiliza la lógica de construcción de grafos adaptándola a ToolContext.
"""
from datetime import datetime
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool

@register_tool("common.build_graph")
class BuildGraphTool(BaseTool):
    platform = None

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        results = ctx.previous_results
        job_id = ctx.job_id
        platform = ctx.platform

        nodes = {}
        edges = []

        def _node(user: dict, role: str = "contact") -> str:
            key = user.get("link_usuario", user.get("username_usuario", "?"))
            if key not in nodes:
                nodes[key] = {
                    "id": key,
                    "platform": platform,
                    "username": user.get("username_usuario"),
                    "nombre": user.get("nombre_usuario"),
                    "foto": user.get("foto_usuario"),
                    "role": role,
                }
            return key

        profile = results.get("profile")
        if profile:
            center = profile.get("url_usuario", profile.get("username", "target"))
            nodes[center] = {
                "id": center,
                "platform": platform,
                "username": profile.get("username"),
                "nombre": profile.get("nombre_completo"),
                "foto": profile.get("foto_perfil"),
                "role": "target",
            }

            for u in results.get("friends", []):
                nid = _node(u)
                edges.append({"src": center, "dst": nid, "type": "FRIEND", "job": job_id})

            for u in results.get("followers", []):
                nid = _node(u)
                edges.append({"src": nid, "dst": center, "type": "FOLLOWER", "job": job_id})

            for u in results.get("followed", []):
                nid = _node(u)
                edges.append({"src": center, "dst": nid, "type": "FOLLOWING", "job": job_id})

            for u in results.get("reactions", []):
                nid = _node(u)
                edges.append({"src": nid, "dst": center, "type": "REACTED", "job": job_id})

            for u in results.get("comments", []):
                nid = _node(u)
                edges.append({"src": nid, "dst": center, "type": "COMMENTED", "job": job_id})

        graph = {"nodes": list(nodes.values()), "edges": edges}
        ctx.previous_results["graph"] = graph

        return ToolResult(
            tool_name=self.name,
            status="ok",
            raw=graph,
            started_at=started,
            finished_at=datetime.now()
        )
