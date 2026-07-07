#!/usr/bin/env python3
"""
x_analyzer.py — Script standalone de análisis de X/Twitter.

Uso:
    python3 x_analyzer.py <url_o_username> [--headless] [--no-headless] [--max-posts N]

Requiere:
    pip install playwright pandas
    playwright install chromium
    pip install scrapling  # opcional

El archivo x_storage_state.json debe estar en el mismo directorio que este script.
"""
import argparse
import asyncio
import logging
import os
import re
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from playwright.async_api import async_playwright

try:
    from scrapling import Selector as ScraplingSelector
except ModuleNotFoundError:
    ScraplingSelector = None  # ponytail: graceful degradation

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
logger = logging.getLogger("x_analyzer")

# ---------------------------------------------------------------------------
# URL Utils (inline)
# ---------------------------------------------------------------------------

def normalize_x_url(url: str) -> str:
    """Normaliza URL o username de X al formato canónico https://x.com/<username>."""
    url = url.strip().lstrip("@")
    if "/" not in url and "://" not in url:
        url = f"https://x.com/{url}"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    p = urllib.parse.urlparse(url)
    host = p.netloc.lower().split(":")[0]
    x_aliases = {"x.com", "www.x.com", "twitter.com", "www.twitter.com", "mobile.twitter.com", "m.twitter.com"}
    if host in x_aliases:
        host = "x.com"
    path = (p.path or "/").replace("//", "/")
    # Strip trailing slash for profiles (keep root as "/")
    if path != "/":
        path = path.rstrip("/")
    return urllib.parse.urlunparse(("https", host, path, "", "", ""))


def extract_x_username(url: str) -> str:
    """Extrae el username de una URL de X."""
    p = urllib.parse.urlparse(url)
    parts = [s for s in p.path.strip("/").split("/") if s]
    skip = {"status", "i", "hashtag", "search", "home", "settings", "messages", "notifications", "followers", "following"}
    if parts and parts[0] not in skip:
        return parts[0]
    return "unknown"


# ---------------------------------------------------------------------------
# User Item Builder (inline)
# ---------------------------------------------------------------------------

def build_user_item(href: str, name: str = "", photo: str = "") -> dict:
    url = normalize_x_url(href)
    username = extract_x_username(url)
    name = (name or "").strip() or username
    photo = (photo or "").strip()
    if photo.startswith("data:"):
        photo = ""
    return {"nombre_usuario": name, "username_usuario": username, "link_usuario": url, "foto_usuario": photo}


# ---------------------------------------------------------------------------
# Session Validator
# ---------------------------------------------------------------------------

async def validate_session(page) -> bool:
    """Verifica que la sesión de X esté activa."""
    await page.goto("https://x.com/", wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    url = page.url.lower()
    if "/login" in url or "signin" in url:
        logger.error("Sesión expirada — redirigido a login: %s", page.url)
        return False
    # Positive check: home nav SVG or avatar
    nav_ok = await page.evaluate("""
        () => {
            const sels = ['nav a[href="/home"]', 'svg[aria-label="Home"]', 'svg[aria-label="Inicio"]',
                          'a[aria-label="Profile"]', 'a[aria-label="Perfil"]'];
            return sels.some(s => document.querySelector(s));
        }
    """)
    if not nav_ok:
        logger.warning("No se detectó navegación de X — posible sesión inválida")
        return False
    logger.info("✅ Sesión de X válida")
    return True


# ---------------------------------------------------------------------------
# Profile Scraper
# ---------------------------------------------------------------------------

async def get_profile_data(page, profile_url: str) -> dict:
    """Extrae nombre, username y foto del perfil de X."""
    url = normalize_x_url(profile_url)
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(4)

    content = await page.content()
    username = extract_x_username(url)
    name = username
    photo = ""

    if ScraplingSelector is not None and len(content) > 500:
        try:
            doc = ScraplingSelector(content=content)
            name_el = doc.css('[data-testid="UserName"] div[dir="ltr"] span, h2[role="heading"] span').first
            if name_el:
                name = (getattr(name_el, "text", None) or "").strip() or name
            img_el = doc.css('[data-testid="UserAvatar-Container-unknown"] img, img[src*="profile_images"]').first
            if img_el:
                photo = (img_el.attrib.get("src") or "").strip()
        except Exception as e:
            logger.debug("Scrapling falló para perfil X: %s", e)

    if name == username or not name:
        try:
            name = await page.evaluate("""
                () => {
                    const sels = ['[data-testid="UserName"] div[dir="ltr"] span',
                                  'h2[role="heading"] span', 'h1 span'];
                    for (const s of sels) {
                        const el = document.querySelector(s);
                        if (el) { const t = el.textContent.trim(); if (t) return t; }
                    }
                    return null;
                }
            """) or username
        except Exception:
            pass

    if not photo:
        try:
            photo = await page.evaluate("""
                () => {
                    const img = document.querySelector('img[src*="profile_images"]');
                    return img ? (img.currentSrc || img.src || '') : '';
                }
            """) or ""
        except Exception:
            pass

    logger.info("Perfil X: @%s (%s)", username, name)
    return {"username": username, "nombre_completo": name, "foto_perfil": photo, "url_usuario": url}


# ---------------------------------------------------------------------------
# List Scraper (followers / following) — scroll + UserCell
# ---------------------------------------------------------------------------

_X_EXCLUDE = ("/status/", "/photo/", "/video/", "/lists/", "/moments/",
               "/search", "/i/", "/compose/", "/settings/", "/notifications/",
               "/messages/", "/bookmarks/", "/explore/", "/home", "/hashtag/")

_JS_USERCELL = r"""
() => {
  const root = document.querySelector('[data-testid="primaryColumn"]') || document;
  const cells = Array.from(root.querySelectorAll('[data-testid="UserCell"]'));
  const out = [];
  for (const cell of cells) {
    const a = cell.querySelector('a[role="link"][href^="/"]');
    if (!a) continue;
    const href = a.getAttribute('href') || '';
    if (!href || href.includes('/status/')) continue;
    const nameSpan = cell.querySelector('div[dir="ltr"] > span:first-child, span[dir="ltr"]');
    const name = nameSpan ? (nameSpan.textContent || '').trim() : '';
    const img = cell.querySelector('img[src*="profile_images"], img');
    const photo = img ? (img.currentSrc || img.src || '') : '';
    out.push({ href, name, photo });
  }
  return out;
}
"""


async def scrap_list(page, profile_url: str, list_type: str) -> List[dict]:
    """Extrae followers o following con scroll infinito."""
    username = extract_x_username(normalize_x_url(profile_url))
    suffix = "followers" if list_type == "followers" else "following"
    target = f"https://x.com/{username}/{suffix}"

    extracted: dict = {}
    logger.info("Navegando a %s ...", target)
    await page.goto(target, wait_until="domcontentloaded")
    await asyncio.sleep(4)

    # Early exit for protected profiles
    body = await page.evaluate("() => document.body.innerText") or ""
    if "protected" in body.lower() or "protegidas" in body.lower():
        logger.warning("Perfil protegido — no se puede extraer '%s'", list_type)
        return []

    no_new, last_total = 0, 0
    for i in range(50):
        try:
            batch = await page.evaluate(_JS_USERCELL) or []
            for rec in batch:
                href = rec.get("href") or ""
                if not href or any(href.startswith(p) for p in _X_EXCLUDE):
                    continue
                url = f"https://x.com{href}"
                item = build_user_item(url, rec.get("name") or "", rec.get("photo") or "")
                uname = item["username_usuario"]
                if not uname or uname.isdigit() or len(uname) < 2 or len(uname) > 50:
                    continue
                key = item["link_usuario"]
                if key not in extracted:
                    extracted[key] = item
        except Exception:
            pass

        try:
            await page.mouse.wheel(0, 800)
        except Exception:
            await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(0.6)

        # Pause every 10 scrolls to avoid rate limiting
        if (i + 1) % 10 == 0:
            await asyncio.sleep(1.5)

        total = len(extracted)
        if total == last_total:
            no_new += 1
            if no_new >= 5:
                logger.info("Sin nuevos usuarios en '%s'. Fin.", list_type)
                break
        else:
            no_new = 0
        last_total = total

        at_bottom = await page.evaluate(
            "() => (window.innerHeight + window.pageYOffset) >= (document.body.scrollHeight - 800)"
        )
        if at_bottom and no_new >= 3:
            break

        logger.info("  Scroll %d: %d usuarios", i + 1, total)

    return list(extracted.values())


# ---------------------------------------------------------------------------
# Comment Scraper — navega a cada post, parsea comentadores, go_back
# ---------------------------------------------------------------------------

_JS_TWEET_LINKS = r"""
() => {
  const arts = Array.from(document.querySelectorAll('article[data-testid="tweet"]'));
  return arts.slice(0, 20).map(a => {
    const link = a.querySelector('a[href*="/status/"]');
    return link ? link.getAttribute('href') : null;
  }).filter(Boolean);
}
"""

_JS_COMMENT_AUTHORS = r"""
() => {
  const arts = Array.from(document.querySelectorAll('article[role="article"], div[data-testid="tweet"]'));
  const out = [];
  for (const art of arts) {
    const a = art.querySelector('a[role="link"][href^="/"]:not([href*="/status/"])');
    if (!a) continue;
    const href = a.getAttribute('href') || '';
    if (!href || href.startsWith('/i/') || href.includes('/status/')) continue;
    const nameSpan = art.querySelector('div[dir="ltr"] > span:first-child, span[dir="ltr"]');
    const name = nameSpan ? (nameSpan.textContent || '').trim() : '';
    const img = art.querySelector('img[src*="profile_images"]');
    const photo = img ? (img.currentSrc || img.src || '') : '';
    out.push({ href, name, photo });
  }
  return out;
}
"""


async def scrap_commenters(page, profile_url: str, max_posts: int = 10) -> List[dict]:
    """Extrae comentadores de posts del perfil: navega a cada post, parsea, go_back."""
    url = normalize_x_url(profile_url)
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(5)

    body = await page.evaluate("() => document.body.innerText") or ""
    if "protected" in body.lower():
        logger.warning("Perfil protegido — no se pueden extraer comentarios")
        return []

    commenters: dict = {}
    posts_done = 0
    scroll_rounds = 0

    while posts_done < max_posts and scroll_rounds < 30:
        post_hrefs = await page.evaluate(_JS_TWEET_LINKS) or []
        post_hrefs = [h for h in post_hrefs if h]

        for href in post_hrefs:
            if posts_done >= max_posts:
                break
            post_url = f"https://x.com{href}"
            # ponytail: normalize post URL as stable key
            post_key = re.sub(r'\?.*', '', post_url)

            scroll_pos = await page.evaluate("window.pageYOffset")
            try:
                # Click into post
                link_el = await page.query_selector(f'a[href="{href}"]')
                if link_el:
                    await link_el.scroll_into_view_if_needed()
                    await link_el.click()
                    await page.wait_for_url(lambda u: "/status/" in u, timeout=5000)
                else:
                    await page.goto(post_url)
            except Exception:
                await page.goto(post_url)
            await asyncio.sleep(5)

            # Scroll to load comments
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(3)

            # Extract comment authors
            try:
                batch = await page.evaluate(_JS_COMMENT_AUTHORS) or []
                for rec in batch:
                    href2 = rec.get("href") or ""
                    if not href2 or any(href2.startswith(p) for p in _X_EXCLUDE):
                        continue
                    item = build_user_item(f"https://x.com{href2}", rec.get("name") or "", rec.get("photo") or "")
                    uname = item["username_usuario"]
                    if not uname or uname.isdigit() or len(uname) < 2 or len(uname) > 50:
                        continue
                    key = item["link_usuario"]
                    if key not in commenters:
                        item["post_url"] = post_key
                        item["interaction_type"] = "comment"
                        commenters[key] = item
            except Exception as e:
                logger.debug("Error extrayendo comentadores del post: %s", e)

            posts_done += 1
            logger.info("  Post %d/%d procesado. Comentadores acumulados: %d", posts_done, max_posts, len(commenters))

            await page.go_back()
            await asyncio.sleep(2)
            await page.evaluate(f"window.scrollTo(0, {scroll_pos})")
            await asyncio.sleep(1)

        # Scroll the main profile page to find more posts
        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(2)
        scroll_rounds += 1

    return list(commenters.values())


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

def export_to_csv(results: dict, output_path: str) -> str:
    rows = []
    profile = results.get("profile") or {}
    if profile:
        rows.append({
            "tipo": "PERFIL", "username": profile.get("username", ""),
            "nombre_completo": profile.get("nombre_completo", ""),
            "url_perfil": profile.get("url_usuario", ""), "foto": profile.get("foto_perfil", ""),
            "interaccion": "", "post_url": "", "texto_comentario": "",
        })

    def _add(lst: List[dict], tipo: str):
        for u in lst:
            rows.append({
                "tipo": tipo, "username": u.get("username_usuario", ""),
                "nombre_completo": u.get("nombre_usuario", ""),
                "url_perfil": u.get("link_usuario", ""), "foto": u.get("foto_usuario", ""),
                "interaccion": u.get("interaction_type", ""),
                "post_url": u.get("post_url", ""), "texto_comentario": "",
            })

    _add(results.get("followers", []), "SEGUIDOR")
    _add(results.get("following", []), "SEGUIDO")
    _add(results.get("commenters", []), "COMENTADOR")

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("CSV exportado: %s (%d filas)", output_path, len(df))
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Análisis de perfil de X/Twitter (standalone)")
    parser.add_argument("profile", help="URL o username (ej: elonmusk o https://x.com/elonmusk)")
    parser.add_argument("--headless", dest="headless", action="store_true", default=True)
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Mostrar ventana del navegador")
    parser.add_argument("--max-posts", type=int, default=10, metavar="N", help="Posts a analizar para comentadores (default: 10)")
    parser.add_argument("--storage-state", default=str(Path(__file__).parent / "x_storage_state.json"), metavar="PATH")
    args = parser.parse_args()

    storage_path = Path(args.storage_state)
    if not storage_path.exists():
        logger.error("No se encontró el storage state: %s", storage_path)
        logger.error("Coloca x_storage_state.json en el mismo directorio que este script.")
        sys.exit(1)

    # ponytail: auto-fallback to headless if no display server
    headless = args.headless
    if not headless and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        logger.warning("⚠️  --no-headless requiere $DISPLAY. No se detectó ninguno.")
        logger.warning("   Usa: xvfb-run python3 x_analyzer.py ...")
        logger.warning("   Continuando en modo headless...")
        headless = True

    profile_url = normalize_x_url(args.profile)
    logger.info("Perfil objetivo: %s", profile_url)
    logger.info("Headless: %s | Max posts: %d", headless, args.max_posts)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            storage_state=str(storage_path),
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        if not await validate_session(page):
            logger.error("Sesión inválida. Actualiza x_storage_state.json.")
            await browser.close()
            sys.exit(1)

        results = {}

        logger.info("=== Extrayendo perfil ===")
        results["profile"] = await get_profile_data(page, profile_url)
        username = results["profile"].get("username", "unknown")

        logger.info("=== Extrayendo seguidores ===")
        results["followers"] = await scrap_list(page, profile_url, "followers")
        logger.info("Seguidores: %d", len(results["followers"]))

        logger.info("=== Extrayendo seguidos ===")
        results["following"] = await scrap_list(page, profile_url, "following")
        logger.info("Seguidos: %d", len(results["following"]))

        logger.info("=== Extrayendo comentadores (max %d posts) ===", args.max_posts)
        results["commenters"] = await scrap_commenters(page, profile_url, max_posts=args.max_posts)
        logger.info("Comentadores: %d", len(results["commenters"]))

        await browser.close()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"x_{username}_{timestamp}.csv"
    export_to_csv(results, csv_name)
    logger.info("✅ Análisis completado → %s", csv_name)


if __name__ == "__main__":
    asyncio.run(main())
