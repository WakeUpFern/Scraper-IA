"""
Implementación real de la herramienta fetch_post_comments_batch.
Navega con Playwright cargando cookies, intercepta respuestas de red, usa Scrapling de fallback y persiste en la base de datos.
"""

import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from playwright.async_api import Response
from scrapling import Selector

from app.tools.base import BaseTool
from app.tools.schemas import FetchCommentsInput, FetchCommentsOutput, CommentInfo
from app.runtime.browser_pool import get_browser
from app.runtime.extractor import NetworkDOMScraper
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class FetchCommentsTool(BaseTool[FetchCommentsInput, FetchCommentsOutput]):
    """Herramienta real fetch_post_comments_batch."""

    def __init__(self):
        super().__init__(
            name="fetch_post_comments_batch",
            description="Obtiene comentarios reales de un post cargando cookies de sesión y guardándolos en base de datos.",
            input_model=FetchCommentsInput,
            output_model=FetchCommentsOutput
        )

    def _parse_network(self, responses: List[Response]) -> Optional[List[Dict[str, Any]]]:
        """Busca respuestas de red JSON con lista de comentarios."""
        for response in responses:
            url = response.url
            try:
                # Instagram comments endpoint
                if "api/v1/media/" in url and "/comments/" in url:
                    data = response.json()
                    comments = data.get("comments", [])
                    results = []
                    for c in comments:
                        c_id = str(c.get("pk"))
                        text = c.get("text", "")
                        user = c.get("user", {})
                        username = user.get("username")
                        full_name = user.get("full_name", username)
                        
                        results.append({
                            "comment_id": c_id,
                            "username": username,
                            "full_name": full_name,
                            "text": text,
                            "published_at": datetime.fromtimestamp(c.get("created_at", datetime.now().timestamp())).isoformat(),
                            "likes": c.get("comment_like_count", 0),
                            "raw_data": c
                        })
                    return results
            except Exception:
                pass
        return None

    def _parse_dom(self, page_source: Selector) -> List[Dict[str, Any]]:
        """DOM Fallback usando selectores de Scrapling para extraer comentarios del post."""
        results = []
        # En Instagram, los comentarios se renderizan como divs con textos de comentarios y nombres de usuario
        # Buscamos patrones comunes de comentarios
        comment_items = page_source.css('ul li div')
        seen_ids = set()
        for idx, item in enumerate(comment_items):
            # Buscar el username del autor del comentario (suele ser el primer link)
            username_elem = item.css('h2 a::text, h3 a::text, span a::text').get()
            comment_text_elem = item.css('span::text').getall()
            
            if username_elem and comment_text_elem:
                username = username_elem.strip().strip("@")
                text = " ".join([t.strip() for t in comment_text_elem if len(t.strip()) > 1])
                
                # Filtrar comentarios repetidos o vacíos
                if username and len(username) > 2 and len(text) > 2:
                    comment_hash = f"{username}:{text[:20]}"
                    if comment_hash not in seen_ids:
                        seen_ids.add(comment_hash)
                        results.append({
                            "comment_id": f"dom_{username}_{idx}",
                            "username": username,
                            "full_name": username,
                            "text": text,
                            "published_at": datetime.now().isoformat(),
                            "likes": 0,
                            "raw_data": {"extracted_via": "dom_fallback"}
                        })
        return results

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: FetchCommentsInput) -> FetchCommentsOutput:
        browser = await get_browser()
        state_path = f"/app/{input_data.platform}_state.json"
        context_args = {}
        if os.path.exists(state_path):
            context_args["storage_state"] = state_path
            logger.info("Cargando cookies para %s desde %s", input_data.platform, state_path)

        context = await browser.new_context(**context_args)
        try:
            page = await context.new_page()
            scraper = NetworkDOMScraper(page)
            
            result = await scraper.scrape(
                url=input_data.post_url,
                network_parser=self._parse_network,
                dom_parser=self._parse_dom
            )
            
            extracted = result["data"] or []
            # Limitar según el lote
            extracted = extracted[:input_data.limit]
            
            comments_list = []
            
            # Obtener ID de la plataforma
            plat_row = await db.fetchrow("SELECT id_plataforma FROM redes.plataforma WHERE codigo = $1", input_data.platform.lower())
            id_plataforma = plat_row["id_plataforma"] if plat_row else 1
            
            # Asegurar que la publicación existe
            post_row = await db.fetchrow(
                "SELECT id_publicacion, id_identidad_autor FROM redes.publicacion WHERE identificador_externo = $1", 
                input_data.post_id
            )
            if post_row:
                id_publicacion = post_row["id_publicacion"]
                id_post_author = post_row["id_identidad_autor"]
            else:
                # Crear post de contingencia
                dummy_author = await db.ensure_digital_identity(input_data.platform, "unknown_author")
                inserted = await db.fetchrow(
                    """
                    INSERT INTO redes.publicacion 
                    (id_analisis, id_plataforma, id_identidad_autor, identificador_externo, url, tipo_publicacion, texto)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING id_publicacion
                    """,
                    id_analisis, id_plataforma, dummy_author, input_data.post_id, input_data.post_url, "post", f"Post {input_data.post_id}"
                )
                id_publicacion = inserted["id_publicacion"]
                id_post_author = dummy_author
            
            tipo_vinculo_id = await db.get_tipo_vinculo_id("commented_on_post")
            
            for item in extracted:
                comment_id = item["comment_id"]
                username = item["username"]
                full_name = item["full_name"]
                text = item["text"]
                published_at_str = item["published_at"]
                
                try:
                    published_at = datetime.fromisoformat(published_at_str)
                except Exception:
                    published_at = datetime.now()
                
                # Asegurar la identidad digital del comentarista
                id_commenter = await db.ensure_digital_identity(
                    platform=input_data.platform,
                    username=username,
                    nombre_publico=full_name
                )
                
                # Guardar comentario en la base de datos real
                try:
                    await db.execute(
                        """
                        INSERT INTO redes.comentario 
                        (id_analisis, id_publicacion, id_plataforma, id_identidad_autor, identificador_externo, texto, fecha_comentario, raw_json)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                        ON CONFLICT (id_plataforma, identificador_externo) DO UPDATE 
                        SET texto = EXCLUDED.texto, raw_json = EXCLUDED.raw_json
                        """,
                        id_analisis, id_publicacion, id_plataforma, id_commenter, comment_id, text, published_at, json.dumps(item)
                    )
                except Exception as db_err:
                    logger.error("Error guardando comentario en DB: %s", db_err)
                
                # Registrar vínculo en la base de datos real: commenter -> commented_on_post -> post_author
                if id_post_author and id_commenter != id_post_author:
                    try:
                        await db.execute(
                            """
                            INSERT INTO redes.vinculo_social 
                            (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo, raw_json)
                            VALUES ($1, $2, $3, $4, $5)
                            ON CONFLICT (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo) DO NOTHING
                            """,
                            id_analisis, id_commenter, id_post_author, tipo_vinculo_id, json.dumps({"post_id": input_data.post_id})
                        )
                    except Exception as db_err:
                        logger.error("Error guardando vinculo_social de comentario en DB: %s", db_err)

                # Registrar en mock_db local para compatibilidad
                mock_db.add_comentario({
                    "id_analisis": id_analisis,
                    "id_tool_run": len(mock_db.tool_runs),
                    "post_id": input_data.post_id,
                    "author": username,
                    "text": text
                })
                
                mock_db.add_vinculo_social({
                    "id_analisis": id_analisis,
                    "id_tool_run": len(mock_db.tool_runs),
                    "source_username": username,
                    "target_username": input_data.post_id,
                    "type": "commented_on_post",
                    "weight": 3.0
                })
                
                comments_list.append(CommentInfo(
                    comment_id=comment_id,
                    author_username=username,
                    author_name=full_name,
                    author_profile_url=f"https://{input_data.platform}.com/{username}",
                    text=text,
                    published_at=published_at_str,
                    like_count=item["likes"]
                ))

            # Guardar evidencia
            await self.save_raw_evidence(
                id_analisis=id_analisis,
                id_tool_run=None,
                evidence_type=result["strategy"],
                platform=input_data.platform,
                source_url=input_data.post_url,
                raw_json=result["raw_evidence"]
            )
            
            return FetchCommentsOutput(
                comments=comments_list,
                next_cursor=None,
                total_fetched=len(comments_list),
                extractor_strategy=result["strategy"],
                parser_version="v3.0.0"
            )
        finally:
            await context.close()
