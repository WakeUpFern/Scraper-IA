"""
app/tools/common/persist_results.py — Herramienta de persistencia en la base de datos relacional.
ponytail: Upsertea identidades y vínculos en personas.identidad_digital y redes.vinculo_social de manera directa y minimalista.
"""
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from app.tools.base import BaseTool, ToolContext, ToolResult
from app.tools.registry import register_tool

logger = logging.getLogger("scr4per.persist")

@register_tool("common.persist_results")
class PersistResultsTool(BaseTool):
    platform = None

    async def run(self, ctx: ToolContext) -> ToolResult:
        started = datetime.now()
        pool = ctx.db_pool
        if not pool:
            logger.warning("[job %s] No hay conexión a base de datos (db_pool es None). Omitiendo persistencia.", ctx.job_id)
            return ToolResult(self.name, "ok", started_at=started, finished_at=datetime.now())

        # 1. Determinar ID de plataforma
        platform_map = {"facebook": 1, "instagram": 2, "x": 3, "twitter": 3}
        platform_id = platform_map.get(ctx.platform.lower())
        if not platform_id:
            logger.error("[job %s] Plataforma '%s' desconocida, no se puede persistir", ctx.job_id, ctx.platform)
            return ToolResult(self.name, "failed", error=f"Plataforma {ctx.platform} desconocida", started_at=started)

        results = ctx.previous_results

        # 2. Upsert del objetivo principal (Target)
        profile = results.get("profile") or {}
        # ponytail: Valores por defecto consistentes para el target
        target_username = profile.get("username") or ctx.username or ctx.target_url.split("/")[-1]
        target_url = profile.get("url_usuario") or profile.get("profile_url") or profile.get("url") or ctx.target_url
        target_display_name = profile.get("nombre_completo") or profile.get("display_name") or target_username
        target_external_id = profile.get("external_id")
        target_desc = profile.get("descripcion") or profile.get("bio")

        id_target = await self._upsert_identidad(
            pool, platform_id, target_username, target_url, target_display_name, target_external_id, target_desc, profile
        )
        logger.info("[job %s] Target persistido con id_identidad_digital: %s", ctx.job_id, id_target)

        # 3. Procesar y persistir relaciones
        # Amigos (Facebook)
        friends = results.get("friends") or []
        for item in friends:
            id_related = await self._upsert_related_item(pool, platform_id, item)
            # Amigos en Facebook: Bidireccional (A -> B y B -> A)
            await self._upsert_vinculo(pool, ctx.job_id, id_target, id_related, 1, item) # 1 = follows
            await self._upsert_vinculo(pool, ctx.job_id, id_related, id_target, 1, item)

        # Seguidores (Followers)
        followers = results.get("followers") or []
        for item in followers:
            id_related = await self._upsert_related_item(pool, platform_id, item)
            # Seguidor: Relacionado -> Target (Sigue a)
            await self._upsert_vinculo(pool, ctx.job_id, id_related, id_target, 1, item)

        # Seguidos (Following)
        followed = results.get("followed") or []
        for item in followed:
            id_related = await self._upsert_related_item(pool, platform_id, item)
            # Seguido: Target -> Relacionado (Sigue a)
            await self._upsert_vinculo(pool, ctx.job_id, id_target, id_related, 1, item)

        # Reacciones (Liked)
        reactions = results.get("reactions") or []
        for item in reactions:
            id_related = await self._upsert_related_item(pool, platform_id, item)
            # Reacción: Relacionado -> Target (Me gusta en post)
            await self._upsert_vinculo(pool, ctx.job_id, id_related, id_target, 3, item) # 3 = liked_post

        # Comentarios (Commented)
        comments = results.get("comments") or []
        for item in comments:
            id_related = await self._upsert_related_item(pool, platform_id, item)
            # Comentario: Relacionado -> Target (Comentó en post)
            await self._upsert_vinculo(pool, ctx.job_id, id_related, id_target, 2, item) # 2 = commented_on_post

        return ToolResult(self.name, "ok", started_at=started, finished_at=datetime.now())

    async def _upsert_related_item(self, pool, platform_id: int, item: dict) -> int:
        username = item.get("username_usuario") or item.get("username")
        url = item.get("link_usuario") or item.get("url") or item.get("profile_url")
        display_name = item.get("nombre_usuario") or item.get("display_name") or username
        external_id = item.get("external_id")
        desc = item.get("descripcion") or item.get("bio")
        return await self._upsert_identidad(pool, platform_id, username, url, display_name, external_id, desc, item)

    async def _upsert_identidad(self, pool, platform_id: int, username: str, url: str,
                                 display_name: str, external_id: str, desc: str, raw: dict) -> int:
        # ponytail: SELECT selectivo antes de INSERT/UPDATE evita problemas con múltiples índices únicos independientes.
        row = None
        if external_id:
            row = await pool.fetchrow(
                "SELECT id_identidad_digital FROM personas.identidad_digital WHERE id_plataforma = $1 AND identificador_externo = $2",
                platform_id, external_id
            )
        if not row and username:
            row = await pool.fetchrow(
                "SELECT id_identidad_digital FROM personas.identidad_digital WHERE id_plataforma = $1 AND username = $2",
                platform_id, username
            )

        if row:
            id_val = row["id_identidad_digital"]
            await pool.execute(
                """
                UPDATE personas.identidad_digital
                SET username = COALESCE($2, username),
                    usuario_url = COALESCE($3, usuario_url),
                    nombre_publico = COALESCE($4, nombre_publico),
                    identificador_externo = COALESCE($5, identificador_externo),
                    descripcion = COALESCE($6, descripcion),
                    raw_json = $7,
                    fecha_modificacion = NOW()
                WHERE id_identidad_digital = $1
                """,
                id_val, username, url, display_name, external_id, desc, json.dumps(raw)
            )
            return id_val
        else:
            row = await pool.fetchrow(
                """
                INSERT INTO personas.identidad_digital (
                    id_plataforma, username, usuario_url, nombre_publico,
                    identificador_externo, descripcion, raw_json, estado, fecha_creacion
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, 'activo', NOW())
                RETURNING id_identidad_digital
                """,
                platform_id, username, url, display_name, external_id, desc, json.dumps(raw)
            )
            return row["id_identidad_digital"]

    async def _upsert_vinculo(self, pool, id_analisis: int, id_origen: int, id_destino: int,
                              id_tipo_vinculo: int, raw: dict) -> None:
        # Evitar auto-vinculación accidental
        if id_origen == id_destino:
            return
        await pool.execute(
            """
            INSERT INTO redes.vinculo_social (
                id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo, fecha_observacion, vigente, raw_json
            )
            VALUES ($1, $2, $3, $4, NOW(), TRUE, $5)
            ON CONFLICT (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo)
            DO UPDATE SET vigente = TRUE, raw_json = EXCLUDED.raw_json
            """,
            id_analisis, id_origen, id_destino, id_tipo_vinculo, json.dumps(raw)
        )
