"""
Pool de navegadores de Playwright para Scr4per v3.
Gestiona el ciclo de vida del navegador Chromium de manera global y asíncrona.
"""

import logging
from playwright.async_api import async_playwright, Browser

logger = logging.getLogger(__name__)

# Singletons de Playwright
_playwright_instance = None
_browser_instance = None


async def get_browser() -> Browser:
    """Devuelve la instancia única del navegador, levantándola si no existe."""
    global _playwright_instance, _browser_instance
    if _browser_instance is None:
        logger.info("Iniciando instancia global de Playwright (Chromium)...")
        _playwright_instance = await async_playwright().start()
        _browser_instance = await _playwright_instance.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"]
        )
    return _browser_instance


async def close_browser_pool() -> None:
    """Libera el pool de navegadores en el apagado del microservicio."""
    global _playwright_instance, _browser_instance
    if _browser_instance is not None:
        logger.info("Cerrando navegador global de Playwright...")
        await _browser_instance.close()
        _browser_instance = None
    if _playwright_instance is not None:
        await _playwright_instance.stop()
        _playwright_instance = None
