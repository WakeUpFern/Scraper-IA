"""
Implementación real de la herramienta fetch_following_batch.
Navega con Playwright cargando cookies, intercepta respuestas de red, usa Scrapling de fallback y persiste en la base de datos.
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from playwright.async_api import Response
from scrapling import Selector

from app.tools.base import BaseTool
from app.tools.schemas import FetchFollowingInput, FetchFollowingOutput, FollowerInfo
from app.runtime.browser_pool import get_browser
from app.runtime.extractor import NetworkDOMScraper
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class FetchFollowingTool(BaseTool[FetchFollowingInput, FetchFollowingOutput]):
    """Herramienta real fetch_following_batch."""

    def __init__(self):
        super().__init__(
            name="fetch_following_batch",
            description="Obtiene cuentas seguidas reales por un perfil cargando cookies de sesión y guardándolas en base de datos.",
            input_model=FetchFollowingInput,
            output_model=FetchFollowingOutput
        )

    def _parse_network(self, responses: List[Response]) -> Optional[List[Dict[str, Any]]]:
        """Busca respuestas de red JSON con lista de seguidos."""
        for response in responses:
            url = response.url
            try:
                # Instagram following API endpoint
                if "api/v1/friendships/" in url and "/following/" in url:
                    data = response.json()
                    users = data.get("users", [])
                    return [
                        {
                            "username": u["username"],
                            "full_name": u.get("full_name", u["username"]),
                            "profile_pic": u.get("profile_pic_url"),
                            "id_externo": str(u["pk"])
                        }
                        for u in users
                    ]
            except Exception:
                pass
        return None

    def _parse_dom(self, page_source: Selector) -> List[Dict[str, Any]]:
        """DOM Fallback usando selectores de Scrapling para extraer seguidos de la lista renderizada."""
        results = []
        # Buscar enlaces de usuario en diálogos emergentes o listas
        items = page_source.css('div[role="dialog"] a[href*="/"], ul li a[href*="/"]')
        seen = set()
        for item in items:
            href = item.attrib.get("href", "")
            # Extraer username del href
            parts = [p for p in href.split("/") if p]
            if parts:
                username = parts[-1].split("?")[0].strip("@")
                # Evitar páginas internas o del sistema
                if username not in ("explore", "direct", "emails", "developer", "about", "blog", "jobs", "help", "api", "privacy", "terms", "locations", "instagram", "facebook", "twitter"):
                    if username not in seen and len(username) > 2:
                        seen.add(username)
                        results.append({
                            "username": username,
                            "full_name": item.text or username,
                            "profile_pic": None,
                            "id_externo": None
                        })
        return results

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: FetchFollowingInput) -> FetchFollowingOutput:
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
            
            url = f"https://www.{input_data.platform}.com/{input_data.username}/following/"
            
            result = await scraper.scrape(
                url=url,
                network_parser=self._parse_network,
                dom_parser=self._parse_dom
            )
            
            extracted = result["data"] or []
            # Limitar según el lote
            extracted = extracted[:input_data.limit]
            
            following_list = []
            
            # Asegurar la identidad digital del target
            id_target = await db.ensure_digital_identity(input_data.platform, input_data.username)
            tipo_vinculo_id = await db.get_tipo_vinculo_id("follows")
            
            for item in extracted:
                username = item["username"]
                full_name = item["full_name"]
                
                # Asegurar la identidad digital de la cuenta seguida
                id_following = await db.ensure_digital_identity(
                    platform=input_data.platform,
                    username=username,
                    nombre_publico=full_name
                )
                
                # Guardar el vínculo en la base de datos real: id_target -> sigue a -> id_following
                try:
                    await db.execute(
                        """
                        INSERT INTO redes.vinculo_social 
                        (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo, raw_json)
                        VALUES ($1, $2, $3, $4, $5)
                        ON CONFLICT (id_analisis, id_identidad_origen, id_identidad_destino, id_tipo_vinculo) DO NOTHING
                        """,
                        id_analisis, id_target, id_following, tipo_vinculo_id, json.dumps(item)
                    )
                except Exception as db_err:
                    logger.error("Error guardando vinculo_social en DB: %s", db_err)

                # Registrar en mock_db local para compatibilidad
                mock_db.add_vinculo_social({
                    "id_analisis": id_analisis,
                    "id_tool_run": len(mock_db.tool_runs),
                    "source_username": input_data.username,
                    "target_username": username,
                    "type": "follows",
                    "weight": 1.0
                })
                
                following_list.append(FollowerInfo(
                    username=username,
                    nombre_publico=full_name,
                    profile_url=f"https://{input_data.platform}.com/{username}",
                    foto_url=item.get("profile_pic")
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
            
            return FetchFollowingOutput(
                following=following_list,
                next_cursor=None,
                total_fetched=len(following_list),
                extractor_strategy=result["strategy"],
                parser_version="v3.0.0"
            )
        finally:
            await context.close()
