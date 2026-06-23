"""
Clase base de extracción que implementa la regla: primero red, DOM como fallback.
Utiliza Playwright para navegación e interceptación, y Scrapling para parseo del DOM.
"""

import logging
from typing import Any, Callable, Dict, List, Optional
from playwright.async_api import Page, Response
from scrapling import Selector

logger = logging.getLogger(__name__)


class NetworkDOMScraper:
    """
    Controla el flujo híbrido de obtención de datos para un objetivo.
    Registra respuestas de red y las evalúa antes de procesar el HTML.
    """

    def __init__(self, page: Page):
        self.page = page
        self.captured_responses: List[Response] = []
        
        # Interceptar tráfico de red
        self.page.on("response", self._on_response)

    def _on_response(self, response: Response) -> None:
        """Callback al recibir cualquier respuesta HTTP de red."""
        try:
            content_type = response.headers.get("content-type", "")
            # Coleccionar respuestas JSON válidas
            if "application/json" in content_type:
                self.captured_responses.append(response)
        except Exception:
            pass

    async def scrape(
        self,
        url: str,
        network_parser: Callable[[List[Response]], Optional[Dict[str, Any]]],
        dom_parser: Callable[[Selector], Dict[str, Any]],
        wait_until: str = "networkidle"
    ) -> Dict[str, Any]:
        """
        Navega a la URL y ejecuta en cascada los métodos de parseo.
        """
        self.captured_responses.clear()
        logger.info("Navegando a %s", url)
        
        await self.page.goto(url, wait_until=wait_until)

        # 1. Intentar Extracción de Red (Network-first)
        try:
            network_data = network_parser(self.captured_responses)
            if network_data:
                logger.info("Extracción exitosa vía interceptación de red (Network-first)")
                
                # Obtener los cuerpos de las respuestas para evidencia
                evidence_raw = []
                for resp in self.captured_responses:
                    if resp.status == 200:
                        try:
                            body = await resp.json()
                            evidence_raw.append({"url": resp.url, "body": body})
                        except Exception:
                            pass
                            
                return {
                    "data": network_data,
                    "strategy": "network_capture",
                    "raw_evidence": evidence_raw
                }
        except Exception as e:
            logger.warning("Fallo al procesar respuestas de red: %s. Cayendo a DOM Fallback.", e)

        # 2. DOM Fallback (Scrapling)
        logger.info("Ejecutando DOM Fallback en el HTML renderizado")
        html = await self.page.content()
        
        # Parsear con el selector de Scrapling
        selector = Selector(html)
        dom_data = dom_parser(selector)
        
        return {
            "data": dom_data,
            "strategy": "dom_fallback",
            "raw_evidence": [{"url": url, "html": html}]
        }
