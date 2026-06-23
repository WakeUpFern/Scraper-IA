"""
Implementación real de la herramienta fetch_recent_posts.
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
from app.tools.schemas import FetchRecentPostsInput, FetchRecentPostsOutput, PostInfo
from app.runtime.browser_pool import get_browser
from app.runtime.extractor import NetworkDOMScraper
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class FetchRecentPostsTool(BaseTool[FetchRecentPostsInput, FetchRecentPostsOutput]):
    """Herramienta real fetch_recent_posts."""

    def __init__(self):
        super().__init__(
            name="fetch_recent_posts",
            description="Obtiene publicaciones recientes reales de una cuenta cargando cookies de sesión y guardándolas en base de datos.",
            input_model=FetchRecentPostsInput,
            output_model=FetchRecentPostsOutput
        )

    def _parse_network(self, responses: List[Response]) -> Optional[List[Dict[str, Any]]]:
        """Busca respuestas de red JSON con lista de publicaciones."""
        for response in responses:
            url = response.url
            try:
                # Instagram user feed endpoint
                if "api/v1/feed/user/" in url:
                    data = response.json()
                    items = data.get("items", [])
                    results = []
                    for item in items:
                        post_id = item.get("code") or str(item.get("pk"))
                        caption = item.get("caption") or {}
                        text = caption.get("text", "")
                        
                        # Buscar métricas
                        likes = item.get("like_count", 0)
                        comments = item.get("comment_count", 0)
                        
                        results.append({
                            "post_id": post_id,
                            "url": f"https://www.instagram.com/p/{post_id}/",
                            "text": text,
                            "published_at": datetime.fromtimestamp(item.get("taken_at", datetime.now().timestamp())).isoformat(),
                            "likes": likes,
                            "comments": comments,
                            "shares": 0,
                            "raw_data": item
                        })
                    return results
            except Exception:
                pass
        return None

    def _parse_dom(self, page_source: Selector) -> List[Dict[str, Any]]:
        """DOM Fallback usando selectores de Scrapling para extraer publicaciones del feed renderizado."""
        results = []
        # Buscar enlaces de publicaciones tipo /p/ID/ en Instagram
        links = page_source.css('a[href*="/p/"]')
        seen = set()
        for idx, link in enumerate(links):
            href = link.attrib.get("href", "")
            # Limpiar href
            parts = [p for p in href.split("/") if p]
            if parts:
                post_id = parts[-1].split("?")[0]
                if post_id not in seen and len(post_id) > 3:
                    seen.add(post_id)
                    # En Instagram, el texto alternativo de las imágenes suele contener la descripción del post
                    img_alt = link.css('img::attr(alt)').get() or ""
                    results.append({
                        "post_id": post_id,
                        "url": f"https://www.instagram.com/p/{post_id}/",
                        "text": img_alt.strip(),
                        "published_at": datetime.now().isoformat(),
                        "likes": 0,
                        "comments": 0,
                        "shares": 0,
                        "raw_data": {"extracted_via": "dom_fallback_link"}
                    })
        return results

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: FetchRecentPostsInput) -> FetchRecentPostsOutput:
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
            
            url = f"https://www.{input_data.platform}.com/{input_data.username}/"
            
            result = await scraper.scrape(
                url=url,
                network_parser=self._parse_network,
                dom_parser=self._parse_dom
            )
            
            extracted = result["data"] or []
            # Limitar según el lote
            extracted = extracted[:input_data.limit]
            
            posts_list = []
            
            # Asegurar la identidad digital de la cuenta autor
            id_autor = await db.ensure_digital_identity(input_data.platform, input_data.username)
            
            # Obtener ID de la plataforma
            plat_row = await db.fetchrow("SELECT id_plataforma FROM redes.plataforma WHERE codigo = $1", input_data.platform.lower())
            id_plataforma = plat_row["id_plataforma"] if plat_row else 1
            
            for item in extracted:
                post_id = item["post_id"]
                post_url = item["url"]
                text = item["text"]
                published_at_str = item["published_at"]
                
                try:
                    published_at = datetime.fromisoformat(published_at_str)
                except Exception:
                    published_at = datetime.now()
                
                # Guardar en redes.publicacion en PostgreSQL
                try:
                    await db.execute(
                        """
                        INSERT INTO redes.publicacion 
                        (id_analisis, id_plataforma, id_identidad_autor, identificador_externo, url, tipo_publicacion, texto, fecha_publicacion, raw_json)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                        ON CONFLICT (id_plataforma, identificador_externo) DO UPDATE 
                        SET texto = EXCLUDED.texto, raw_json = EXCLUDED.raw_json
                        """,
                        id_analisis, id_plataforma, id_autor, post_id, post_url, "post", text, published_at, json.dumps(item)
                    )
                except Exception as db_err:
                    logger.error("Error guardando publicacion en DB: %s", db_err)

                # Registrar en mock_db local para compatibilidad
                mock_db.add_publicacion({
                    "id_analisis": id_analisis,
                    "id_tool_run": len(mock_db.tool_runs),
                    "post_id": post_id,
                    "author": input_data.username,
                    "content": text,
                    "metrics": {"likes": item["likes"], "comments": item["comments"]}
                })
                
                posts_list.append(PostInfo(
                    post_id=post_id,
                    post_url=post_url,
                    content=text,
                    published_at=published_at_str,
                    like_count=item["likes"],
                    comment_count=item["comments"],
                    share_count=item["shares"],
                    raw_data=item["raw_data"]
                ))

            # Guardar evidencia
            await self.save_raw_evidence(
                id_analisis=id_analisis,
                id_tool_run=None,
                evidence_type=result["strategy"],
                platform=input_data.platform,
                source_url=url,
                raw_json=result["raw_evidence"]
            )
            
            return FetchRecentPostsOutput(
                posts=posts_list,
                total_fetched=len(posts_list),
                extractor_strategy=result["strategy"],
                parser_version="v3.0.0"
            )
        finally:
            await context.close()
