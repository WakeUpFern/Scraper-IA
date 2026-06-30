"""
app/tools/common/export_excel.py — Herramienta para exportar el perfil y relaciones a un archivo Excel (.xlsx).
ponytail: Genera un libro de Excel de múltiples hojas con pandas + openpyxl de manera sencilla.
"""
import os
import pandas as pd
from datetime import datetime
from pathlib import Path
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool

ARTIFACTS_DIR = Path(os.getenv("ARTIFACTS_DIR", "/tmp/scr4per_artifacts"))

@register_tool("common.export_excel")
class ExportExcelTool(BaseTool):
    platform = None

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        job_id = ctx.job_id
        results = ctx.previous_results

        # Asegurar directorio de destino
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        xlsx_path = ARTIFACTS_DIR / f"job_{job_id}_profile.xlsx"

        # Crear escritor Excel usando openpyxl
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            # 1. Hoja Perfil
            profile = results.get("profile") or {}
            profile_data = []
            for k, v in profile.items():
                profile_data.append({"Campo": k, "Valor": str(v)})
            if not profile_data:
                profile_data.append({"Campo": "Información", "Valor": "No se obtuvieron datos de perfil"})
            df_profile = pd.DataFrame(profile_data)
            df_profile.to_excel(writer, sheet_name="Perfil", index=False)

            # ponytail: Mapeo de nombres de columnas técnicos a legibles de forma robusta con rename()
            rename_map = {
                "nombre_usuario": "Nombre",
                "username_usuario": "Username",
                "link_usuario": "URL de Perfil",
                "foto_usuario": "Foto de Perfil",
                "interaction_type": "Tipo de Interacción",
                "comment_text": "Comentario",
                "texto": "Comentario",
                "post_url": "URL de Publicación"
            }

            # 2. Hoja Amigos (solo aplica para Facebook, pero la creamos si tiene datos)
            friends = results.get("friends") or []
            df_friends = pd.DataFrame(friends)
            if not df_friends.empty:
                df_friends.rename(columns=rename_map, inplace=True)
            df_friends.to_excel(writer, sheet_name="Amigos", index=False)

            # 3. Hoja Seguidores
            followers = results.get("followers") or []
            df_followers = pd.DataFrame(followers)
            if not df_followers.empty:
                df_followers.rename(columns=rename_map, inplace=True)
            df_followers.to_excel(writer, sheet_name="Seguidores", index=False)

            # 4. Hoja Seguidos
            followed = results.get("followed") or []
            df_followed = pd.DataFrame(followed)
            if not df_followed.empty:
                df_followed.rename(columns=rename_map, inplace=True)
            df_followed.to_excel(writer, sheet_name="Seguidos", index=False)

            # 5. Hoja Reacciones
            reactions = results.get("reactions") or []
            df_reactions = pd.DataFrame(reactions)
            if not df_reactions.empty:
                df_reactions.rename(columns=rename_map, inplace=True)
            df_reactions.to_excel(writer, sheet_name="Reacciones", index=False)

            # 6. Hoja Comentarios
            comments = results.get("comments") or []
            df_comments = pd.DataFrame(comments)
            if not df_comments.empty:
                df_comments.rename(columns=rename_map, inplace=True)
            df_comments.to_excel(writer, sheet_name="Comentarios", index=False)


        artifacts = [
            {"name": xlsx_path.name, "path": str(xlsx_path), "type": "excel"}
        ]
        ctx.previous_results["artifacts"].extend(artifacts)

        return ToolResult(
            tool_name=self.name,
            status="ok",
            artifacts=artifacts,
            started_at=started,
            finished_at=datetime.now()
        )
