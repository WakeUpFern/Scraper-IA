@"""
Script auxiliar para iniciar sesión de forma interactiva y guardar el estado (cookies y storage).
Ayuda a evitar bloqueos de login y a reutilizar sesiones autenticadas en el scraper.
"""

import asyncio
from playwright.async_api import async_playwright


async def run():
    async with async_playwright() as p:
        # Abrir navegador visible (headed) para interacción del usuario
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        print("\n" + "=" * 60)
        print("1. Se abrirá una ventana del navegador.")
        print("2. Por favor, inicia sesión manualmente en Facebook.")
        print("3. Una vez logueado, CIERRA la ventana del navegador.")
        print("=" * 60 + "\n")
        
        # Ir a la página principal de login
        await page.goto("https://www.facebook.com")
        
        # Esperar a que la página se cierre manualmente por el usuario
        closed_event = asyncio.Event()
        page.on("close", lambda p: closed_event.set())
        
        await closed_event.wait()
        
        # Guardar el estado de sesión actual antes de apagar
        await context.storage_state(path="facebook_state.json")
        print("\n[!] Sesión e inicio de sesión guardados con éxito en 'facebook_state.json'.")
        
        await browser.close()


if __name__ == "__main__":
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        print("\nProceso cancelado por el usuario.")
