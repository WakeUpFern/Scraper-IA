"""
Implementación real de la herramienta fetch_profile_snapshot.
Navega con Playwright cargando cookies, intercepta red, usa Scrapling de fallback y persiste en base de datos.
"""

import os
import json
import logging
import re
from typing import Any, Dict, List, Optional
from playwright.async_api import Response
from scrapling import Selector

from app.tools.base import BaseTool
from app.tools.schemas import FetchProfileInput, FetchProfileOutput
from app.runtime.browser_pool import get_browser
from app.runtime.extractor import NetworkDOMScraper
from app.tools import mock_db
from app.runtime import db

logger = logging.getLogger(__name__)


class FetchProfileTool(BaseTool[FetchProfileInput, FetchProfileOutput]):
    """Herramienta real fetch_profile_snapshot."""

    def __init__(self):
        super().__init__(
            name="fetch_profile_snapshot",
            description="Obtiene snapshot real de un perfil de red social cargando cookies de sesión y extrayendo datos vía Red o DOM.",
            input_model=FetchProfileInput,
            output_model=FetchProfileOutput
        )

    def _parse_network(self, responses: List[Response]) -> Optional[Dict[str, Any]]:
        """Busca respuestas de red JSON con datos del perfil."""
        for response in responses:
            url = response.url
            try:
                # Instagram Web Profile API
                if "api/v1/users/web_profile_info" in url:
                    data = response.json()
                    user = data["data"]["user"]
                    return {
                        "username": user["username"],
                        "full_name": user["full_name"],
                        "biography": user["biography"],
                        "profile_pic": user["profile_pic_url"],
                        "followers": user["edge_followed_by"]["count"],
                        "following": user["edge_follow"]["count"],
                        "external_url": user.get("external_url")
                    }
                # Facebook Profile API (GraphQL o endpoints similares)
                elif "api/graphql" in url or "facebook.com/api" in url:
                    data = response.json()
                    # Buscar patrones comunes en las respuestas GraphQL de FB
                    for entry in data if isinstance(data, list) else [data]:
                        if "user" in entry.get("data", {}):
                            user = entry["data"]["user"]
                            return {
                                "username": user.get("username", ""),
                                "full_name": user.get("name", ""),
                                "biography": user.get("bio", {}).get("text", ""),
                                "profile_pic": user.get("profile_picture", {}).get("uri", ""),
                                "followers": user.get("followers", {}).get("count", 0),
                                "following": user.get("friends", {}).get("count", 0),
                                "external_url": None
                            }
            except Exception:
                pass
        return None

    def _parse_dom(self, page_source: Selector) -> Dict[str, Any]:
        """DOM Fallback usando selectores de Scrapling."""
        # selectores universales y tolerantes a cambios de diseño (reglas adaptativas)
        # Buscar meta tags que a veces contienen información estructurada de OpenGraph
        og_title = page_source.css('meta[property="og:title"]::attr(content)').get()
        og_description = page_source.css('meta[property="og:description"]::attr(content)').get()
        og_image = page_source.css('meta[property="og:image"]::attr(content)').get()

        # Fallback a selectores estándar
        username = page_source.css('h2::text, h1::text').get() or "unknown"
        full_name = og_title or page_source.css('title::text').get() or ""
        bio = og_description or page_source.css('div[data-testid="UserDescription"]::text, header section div span::text').get() or ""
        profile_pic = og_image or page_source.css('header img::attr(src), img[alt*="profile"]::attr(src)').get() or ""

        # Intentar extraer métricas del OG description o texto
        followers = 0
        following = 0
        if og_description:
            # Ejemplo: "120 Followers, 300 Following, 40 Posts..."
            m = re.search(r'([\d\.,]+)\s*(seguid|follower)', og_description, re.IGNORECASE)
            if m:
                followers = int(m.group(1).replace(",", "").replace(".", ""))
            m2 = re.search(r'([\d\.,]+)\s*(seguid|following)', og_description, re.IGNORECASE)
            if m2:
                following = int(m2.group(1).replace(",", "").replace(".", ""))

        return {
            "username": username.strip().strip("@"),
            "full_name": full_name.split("-")[0].strip() if "-" in full_name else full_name.strip(),
            "biography": bio.strip(),
            "profile_pic": profile_pic,
            "followers": followers,
            "following": following,
            "external_url": None
        }

    async def _run(self, id_analisis: int, id_usuario: int | None, input_data: FetchProfileInput) -> FetchProfileOutput:
        browser = await get_browser()
        
        # Cargar cookies de sesión si existen
        state_path = f"/app/{input_data.platform}_state.json"
        context_args = {}
        if os.path.exists(state_path):
            context_args["storage_state"] = state_path
            logger.info("Cargando cookies de sesión para %s desde %s", input_data.platform, state_path)

        context = await browser.new_context(**context_args)
        try:
            page = await context.new_page()
            scraper = NetworkDOMScraper(page)
            
            # Ejecutar navegación e interceptación
            result = await scraper.scrape(
                url=input_data.profile_url,
                network_parser=self._parse_network,
                dom_parser=self._parse_dom
            )
            
            extracted = result["data"]
            
            # 1. Guardar la evidencia cruda
            await self.save_raw_evidence(
                id_analisis=id_analisis,
                id_tool_run=None, # BaseTool lo asocia automáticamente al tool_run actual
                evidence_type=result["strategy"],
                platform=input_data.platform,
                source_url=input_data.profile_url,
                raw_json=result["raw_evidence"]
            )

            # 2. Persistir en base de datos real (redes.identidad_observacion)
            # ponytail: query SQL directa para registrar observaciones
            try:
                await db.execute(
                    """
                    INSERT INTO redes.identidad_observacion
                    (id_analisis, id_tool_run, nombre_publico_observado, username_observado, usuario_url_observada, descripcion_observada, foto_url_observada, metricas_json, raw_json)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    """,
                    id_analisis, 
                    self.current_tool_run_id, # ID del tool run actual
                    extracted["full_name"],
                    extracted["username"],
                    input_data.profile_url,
                    extracted["biography"],
                    extracted["profile_pic"],
                    json.dumps({"followers": extracted["followers"], "following": extracted["following"]}),
                    json.dumps(extracted)
                )
            except Exception as db_err:
                logger.error("Error persistiendo identidad_observacion en DB: %s", db_err)

            # 3. Guardar en el mock_db local por compatibilidad
            mock_db.add_identidad_observada({
                "id_analisis": id_analisis,
                "id_tool_run": len(mock_db.tool_runs),
                "nombre_publico_observado": extracted["full_name"],
                "username_observado": extracted["username"],
                "usuario_url_observada": input_data.profile_url,
                "descripcion_observada": extracted["biography"],
                "foto_url_observada": extracted["profile_pic"],
                "metricas_json": {"followers": extracted["followers"], "following": extracted["following"]},
                "raw_json": extracted
            })

            return FetchProfileOutput(
                username_observado=extracted["username"],
                nombre_publico_observado=extracted["full_name"],
                descripcion_observada=extracted["biography"],
                foto_url_observada=extracted["profile_pic"],
                usuario_url_observada=input_data.profile_url,
                metricas_json={"followers": extracted["followers"], "following": extracted["following"]},
                links_externos=[extracted["external_url"]] if extracted.get("external_url") else [],
                extractor_strategy=result["strategy"],
                parser_version="v3.0.0"
            )
        finally:
            await context.close()
