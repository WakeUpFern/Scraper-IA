"""
scrapers/x/adapter.py

Motor de scraping de X/Twitter extraído de x_analyzer.py (sin cambios funcionales).
Expone run_analysis() como punto de entrada para el worker de la API.
"""
import asyncio
import logging
import os
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from playwright.async_api import async_playwright

try:
    from scrapling import Selector as ScraplingSelector
except ModuleNotFoundError:
    ScraplingSelector = None  # ponytail: graceful degradation

logger = logging.getLogger("scr4per.x")

# ---------------------------------------------------------------------------
# URL utils
# ---------------------------------------------------------------------------

def normalize_x_url(url: str) -> str:
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
    if path != "/":
        path = path.rstrip("/")
    return urllib.parse.urlunparse(("https", host, path, "", "", ""))


def extract_x_username(url: str) -> str:
    p = urllib.parse.urlparse(url)
    parts = [s for s in p.path.strip("/").split("/") if s]
    skip = {"status", "i", "hashtag", "search", "home", "settings", "messages", "notifications", "followers", "following"}
    if parts and parts[0] not in skip:
        return parts[0]
    return "unknown"


def build_user_item(href: str, name: str = "", photo: str = "") -> dict:
    url = normalize_x_url(href)
    username = extract_x_username(url)
    name = (name or "").strip() or username
    photo = (photo or "").strip()
    if photo.startswith("data:"):
        photo = ""
    return {
        "nombre_usuario": name,
        "username_usuario": username,
        "link_usuario": url,
        "foto_usuario": photo
    }


# ---------------------------------------------------------------------------
# Session validator
# ---------------------------------------------------------------------------

async def validate_session(page) -> bool:
    await page.goto("https://x.com/", wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    url = page.url.lower()
    if "/login" in url or "signin" in url:
        logger.error("Sesión expirada — redirigido a login: %s", page.url)
        return False
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
# Profile data
# ---------------------------------------------------------------------------

async def get_profile_data(page, profile_url: str) -> dict:
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
    return {
        "username": username,
        "nombre_completo": name,
        "foto_perfil": photo,
        "url_usuario": url
    }


# ---------------------------------------------------------------------------
# List extraction (followers / following)
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

async def scrap_list(page, profile_url: str, list_type: str, max_items: int = 0) -> List[dict]:
    username = extract_x_username(normalize_x_url(profile_url))
    suffix = "followers" if list_type == "followers" else "following"
    target = f"https://x.com/{username}/{suffix}"

    extracted: dict = {}
    logger.info("Navegando a %s ...", target)
    await page.goto(target, wait_until="domcontentloaded")
    await asyncio.sleep(4)

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

        # Check limit
        total = len(extracted)
        if max_items > 0 and total >= max_items:
            logger.info("Límite de %d alcanzado en '%s'.", max_items, list_type)
            return list(extracted.values())[:max_items]

        try:
            await page.mouse.wheel(0, 800)
        except Exception:
            await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(0.6)

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
# Comment / Commenters scraper
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
            post_key = re.sub(r'\?.*', '', post_url)

            scroll_pos = await page.evaluate("window.pageYOffset")
            try:
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

            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await asyncio.sleep(3)

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

        await page.evaluate("window.scrollBy(0, 800)")
        await asyncio.sleep(2)
        scroll_rounds += 1

    return list(commenters.values())


# ---------------------------------------------------------------------------
# run_analysis — entrypoint para el worker
# ---------------------------------------------------------------------------

async def run_analysis(
    profile_url: str,
    storage_state_path: str,
    scope: dict,
    limits: dict,
    headless: bool = True,
    on_progress=None,
) -> dict:
    """
    Ejecuta el análisis completo de un perfil de X.
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(
            storage_state=storage_state_path,
            viewport={"width": 1280, "height": 720},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        if not await validate_session(page):
            await browser.close()
            raise RuntimeError("Sesión de X inválida o expirada")

        results: dict = {
            "profile": {},
            "friends": [],
            "followers": [],
            "followed": [],
            "reactions": [],
            "comments": []
        }

        if scope.get("profile", True):
            logger.info("=== Extrayendo perfil ===")
            results["profile"] = await get_profile_data(page, profile_url)
            if on_progress:
                on_progress("profile", results["profile"])

        if scope.get("followers", False):
            logger.info("=== Extrayendo seguidores ===")
            results["followers"] = await scrap_list(page, profile_url, "followers", limits.get("max_followers", 0))
            if on_progress:
                on_progress("followers", {"count": len(results["followers"])})

        if scope.get("following", False):
            logger.info("=== Extrayendo seguidos ===")
            results["followed"] = await scrap_list(page, profile_url, "following", limits.get("max_following", 0))
            if on_progress:
                on_progress("following", {"count": len(results["followed"])})

        if scope.get("comments", False):
            max_posts = limits.get("max_photos", 10)
            logger.info("=== Extrayendo comentadores (max %d posts) ===", max_posts)
            commenters = await scrap_commenters(page, profile_url, max_posts=max_posts)
            results["comments"] = commenters
            if on_progress:
                on_progress("engagements", {
                    "reactions": 0,
                    "comments": len(results["comments"]),
                })

        await browser.close()
    return results
