"""
scrapers/instagram/adapter.py

Motor de scraping de Instagram extraído de instagram_analyzer.py (sin cambios funcionales).
Expone run_analysis() como punto de entrada para el worker de la API.
"""
import asyncio
import logging
import os
import re
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from playwright.async_api import async_playwright

try:
    from scrapling import Selector as ScraplingSelector
except ModuleNotFoundError:
    ScraplingSelector = None  # ponytail: graceful degradation

logger = logging.getLogger("scr4per.instagram")

# ---------------------------------------------------------------------------
# URL utils
# ---------------------------------------------------------------------------

def normalize_ig_url(url: str) -> str:
    url = url.strip().lstrip("@")
    if "/" not in url and "://" not in url:
        url = f"https://www.instagram.com/{url}"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    p = urllib.parse.urlparse(url)
    host = p.netloc.lower().split(":")[0]
    ig_aliases = {"instagram.com", "www.instagram.com", "m.instagram.com"}
    if host in ig_aliases:
        host = "www.instagram.com"
    path = (p.path or "/").replace("//", "/")
    if path.count("/") >= 1:
        path = path.rstrip("/") + "/"
    return urllib.parse.urlunparse(("https", host, path, "", "", ""))


def extract_ig_username(url: str) -> str:
    p = urllib.parse.urlparse(url)
    parts = [s for s in p.path.strip("/").split("/") if s]
    skip = {"followers", "following", "p", "reel", "tv", "stories", "explore", "accounts"}
    return parts[0] if parts and parts[0] not in skip else "unknown"


def normalize_post_url(url: str) -> str:
    p = urllib.parse.urlparse(url)
    host = p.netloc.lower()
    ig_aliases = {"instagram.com", "www.instagram.com", "m.instagram.com"}
    if host in ig_aliases:
        host = "www.instagram.com"
    return urllib.parse.urlunparse(("https", host, p.path.rstrip("/"), "", "", ""))


def build_user_item(href: str, name: str = "", photo: str = "") -> dict:
    url = normalize_ig_url(href)
    username = extract_ig_username(url)
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
# DOM selectors
# ---------------------------------------------------------------------------

_MODAL_SELECTORS = [
    'div[role="dialog"]', 'div[aria-modal="true"]',
    'div[class*="ISgrP"]', 'div[class*="_1XyE"]', 'div[class*="x1qjc9v5"]'
]

_JS_MODAL_USERS = """
(selectors) => {
    let dialog = null;
    for (const sel of selectors) {
        dialog = document.querySelector(sel);
        if (dialog) break;
    }
    if (!dialog) return [];
    const rows = Array.from(dialog.querySelectorAll('div[role="dialog"] a[href^="/"], div[aria-modal="true"] a[href^="/"], li a[href^="/"]'));
    const out = [];
    const seen = new Set();
    for (const r of rows) {
        const href = r.getAttribute('href') || '';
        if (!href || href === '/' || seen.has(href)) continue;
        seen.add(href);
        // Find text label (username/name)
        let name = (r.textContent || '').trim();
        // Look for image
        let parent = r.parentElement, img = null, depth = 0;
        while (parent && depth < 4) {
            img = parent.querySelector('img');
            if (img) break;
            parent = parent.parentElement; depth++;
        }
        const src = img ? (img.currentSrc || img.src || '') : '';
        out.push({ href, name, src });
    }
    return out;
}
"""

# ---------------------------------------------------------------------------
# Popups and sessions
# ---------------------------------------------------------------------------

async def dismiss_popups(page) -> None:
    selectors = [
        'button:has-text("Ahora no")', 'button:has-text("Not now")',
        'button:has-text("Aceptar")', 'button:has-text("Allow all cookies")',
        'button:has-text("Permitir cookies")', 'button:has-text("Rechazar cookies opcionales")',
        'button:has-text("Decline optional cookies")',
    ]
    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click(timeout=1000)
                await asyncio.sleep(0.3)
        except Exception:
            continue


async def validate_session(page) -> bool:
    await page.goto("https://www.instagram.com/", wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    await dismiss_popups(page)
    url = page.url.lower()
    if "/accounts/login" in url or "/challenge/" in url or "/checkpoint/" in url:
        logger.error("Sesión expirada o bloqueada: %s", page.url)
        return False
    nav_ok = await page.evaluate("""
        () => {
            const sels = ['nav a[href="/"]', 'svg[aria-label="Home"]', 'svg[aria-label="Inicio"]',
                          'a[href*="/accounts/edit/"]', 'img[alt*="profile picture"]',
                          'img[alt*="foto del perfil"]'];
            return sels.some(s => document.querySelector(s));
        }
    """)
    if not nav_ok:
        logger.warning("No se detectó navegación de Instagram — posible sesión inválida")
        return False
    logger.info("✅ Sesión de Instagram válida")
    return True


# ---------------------------------------------------------------------------
# Profile data
# ---------------------------------------------------------------------------

async def get_profile_data(page, profile_url: str) -> dict:
    url = normalize_ig_url(profile_url)
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_function(
            "() => !!document.querySelector('header') && !!document.querySelector('a[href^=\"/\"]')",
            timeout=12000,
        )
    except Exception:
        await asyncio.sleep(3)
    await dismiss_popups(page)

    username = extract_ig_username(url)
    display_name: Optional[str] = None
    photo = ""
    is_private = False

    content = await page.content()

    if ScraplingSelector is not None and len(content) > 300:
        try:
            private_indicators = [
                "esta cuenta es privada", "this account is private", "cuenta privada",
                "síguela para ver sus fotos", "follow to see their photos",
            ]
            if any(ind in content.lower() for ind in private_indicators):
                is_private = True

            doc = ScraplingSelector(content=content)
            for node in doc.css("header h2, header h1, h1, h2"):
                text = (getattr(node, "text", None) or "").strip()
                if text and text.lower() != username.lower():
                    display_name = text
                    break
            for node in doc.css("header img"):
                alt = (node.attrib.get("alt") or "").lower()
                src = (node.attrib.get("src") or node.attrib.get("data-src") or "").strip()
                if not src or src.startswith("data:"):
                    continue
                if any(k in alt for k in ("story", "highlight", "historia")):
                    continue
                photo = src
                break
        except Exception as e:
            logger.debug("Scrapling falló para perfil IG: %s", e)

    if not display_name:
        try:
            display_name = await page.evaluate("""
                (uname) => {
                    const cands = document.querySelectorAll('header h2, header h1, h1, h2');
                    for (const el of cands) {
                        const t = (el.textContent || '').trim();
                        if (t && t.toLowerCase() !== uname.toLowerCase()) return t;
                    }
                    return uname;
                }
            """, username) or username
        except Exception:
            display_name = username

    if not photo:
        try:
            photo = await page.evaluate("""
                () => {
                    const img = Array.from(document.querySelectorAll('header img, img[alt*="profile" i], img[alt*="perfil" i]')).find(el => {
                        let p = el.parentElement;
                        while (p) {
                            if (p.getAttribute('role') === 'navigation' || p.tagName.toLowerCase() === 'nav') return false;
                            p = p.parentElement;
                        }
                        const alt = (el.getAttribute('alt') || '').toLowerCase();
                        return !alt.includes('story') && !alt.includes('highlight') && !alt.includes('historia');
                    });
                    return img ? (img.currentSrc || img.src || '') : '';
                }
            """) or ""
        except Exception:
            pass

    logger.info("Perfil IG: @%s (%s) | privado=%s", username, display_name, is_private)
    return {
        "username": username,
        "nombre_completo": display_name or username,
        "foto_perfil": photo,
        "url_usuario": url,
        "is_private": is_private,
    }


# ---------------------------------------------------------------------------
# Scroll helpers
# ---------------------------------------------------------------------------

async def _find_scroll_container(page):
    try:
        return await page.evaluate_handle("""
            () => {
                const dialogs = document.querySelectorAll('div[role="dialog"], div[aria-modal="true"]');
                for (const d of dialogs) {
                    for (const child of d.querySelectorAll('*')) {
                        const style = window.getComputedStyle(child);
                        if (child.scrollHeight > child.clientHeight + 50
                            && /(auto|scroll)/.test(style.overflowY + style.overflow)) {
                            return child;
                        }
                    }
                }
                return null;
            }
        """)
    except Exception:
        return None


async def _scroll_modal(page, container, delta: int = 1000) -> None:
    try:
        if container:
            await container.evaluate(f"el => el.scrollBy(0, {delta})")
        else:
            await page.evaluate(f"window.scrollBy(0, {delta})")
    except Exception:
        pass


# ---------------------------------------------------------------------------
# List extraction
# ---------------------------------------------------------------------------

async def scrap_list(page, profile_url: str, list_type: str, main_username: str = "", max_items: int = 0) -> List[dict]:
    url = normalize_ig_url(profile_url)
    logger.info("Navegando a perfil para abrir modal de '%s'...", list_type)
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_function(
            "() => !!document.querySelector('header') && !!document.querySelector('a[href^=\"/\"]')",
            timeout=12000,
        )
    except Exception:
        await asyncio.sleep(3)
    await dismiss_popups(page)

    link_sels = {
        "followers": ['a[href*="/followers/"]', 'a:has-text("seguidores")', 'a:has-text("followers")', 'header a[href*="followers"]'],
        "following": ['a[href*="/following/"]', 'a:has-text("seguidos")', 'a:has-text("following")', 'header a[href*="following"]'],
    }
    opened = False
    for sel in link_sels.get(list_type, []):
        try:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                await asyncio.sleep(3)
                opened = True
                break
        except Exception:
            continue

    if not opened:
        logger.warning("No se pudo abrir modal de '%s'. ¿Perfil privado?", list_type)
        return []

    extracted: dict = {}
    container = await _find_scroll_container(page)

    no_new, last_total = 0, 0
    for i in range(60):
        try:
            batch = await page.evaluate(_JS_MODAL_USERS, _MODAL_SELECTORS) or []
            for rec in batch:
                href = rec.get("href") or ""
                if not href or not href.startswith("/"):
                    continue
                ig_skip = {"/p/", "/reel/", "/explore/", "/accounts/", "/stories/"}
                if any(href.startswith(s) for s in ig_skip):
                    continue
                url_abs = f"https://www.instagram.com{href}"
                item = build_user_item(url_abs, rec.get("name") or "", rec.get("src") or "")
                uname = item["username_usuario"]
                if uname == main_username or uname == "unknown":
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

        await _scroll_modal(page, container, 1000)

        # Adaptive wait: poll for new DOM nodes
        try:
            base = await page.evaluate(_JS_MODAL_USERS, _MODAL_SELECTORS)
            waited = 0
            while waited < 1200:
                await asyncio.sleep(0.2)
                new = await page.evaluate(_JS_MODAL_USERS, _MODAL_SELECTORS)
                if len(new or []) > len(base or []):
                    break
                waited += 200
        except Exception:
            await asyncio.sleep(2.4)

        if (i + 1) % 12 == 0:
            logger.info("Pausa breve (%d usuarios hasta ahora)...", len(extracted))
            await asyncio.sleep(3.5)

        total = len(extracted)
        if total == last_total:
            no_new += 1
            if no_new >= 6:
                logger.info("Sin nuevos usuarios en '%s'. Fin.", list_type)
                break
        else:
            no_new = 0
        last_total = total
        logger.info("  Scroll %d: %d usuarios (%s)", i + 1, total, list_type)

    return list(extracted.values())


# ---------------------------------------------------------------------------
# Post engagements
# ---------------------------------------------------------------------------

def _ig_username_valid(username: str) -> bool:
    return bool(username and re.match(r'^[A-Za-z0-9._]{1,30}$', username))


def _extract_likers_from_payload(payload, owner_username: str, post_url: str) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    owner_l = (owner_username or "").lower()

    def _iter(obj):
        if isinstance(obj, dict):
            yield obj
            for v in obj.values():
                yield from _iter(v)
        elif isinstance(obj, list):
            for item in obj:
                yield from _iter(item)

    for node in _iter(payload):
        username = node.get("username")
        if not isinstance(username, str):
            continue
        username = username.strip()
        if not _ig_username_valid(username) or username.lower() == owner_l:
            continue
        if not any(k in node for k in ("profile_pic_url", "full_name", "is_private", "is_verified", "id")):
            continue
        full_name = node.get("full_name") if isinstance(node.get("full_name"), str) else None
        photo = node.get("profile_pic_url") or node.get("profile_pic_url_hd") or ""
        profile_url = f"https://www.instagram.com/{username}/"
        item = build_user_item(profile_url, full_name or username, photo)
        item["post_url"] = normalize_post_url(post_url)
        item["interaction_type"] = "like"
        key = item.get("link_usuario")
        if key and key not in out:
            out[key] = item

    return out


async def _collect_post_urls(page, profile_url: str, max_posts: int) -> List[str]:
    url = normalize_ig_url(profile_url)
    await page.goto(url, wait_until="domcontentloaded")
    await asyncio.sleep(3)
    await dismiss_popups(page)

    urls: list = []
    sels = ['article a[href*="/p/"]', 'article a[href*="/reel/"]', 'a[href*="/p/"]', 'a[href*="/reel/"]']
    scrolls, no_new = 0, 0

    while len(urls) < max_posts and scrolls < 10 and no_new < 3:
        before = len(urls)
        for sel in sels:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    if len(urls) >= max_posts:
                        break
                    href = await el.get_attribute("href")
                    if href:
                        full = f"https://www.instagram.com{href}" if href.startswith("/") else href
                        if ("/p/" in full or "/reel/" in full) and full not in urls:
                            urls.append(full)
            except Exception:
                continue

        await page.evaluate("window.scrollBy(0, window.innerHeight * 0.8)")
        await asyncio.sleep(2)
        scrolls += 1

        if len(urls) == before:
            no_new += 1
        else:
            no_new = 0

    return urls[:max_posts]


async def scrap_post_engagements(page, profile_url: str, username: str, max_posts: int = 5) -> Dict[str, List[dict]]:
    post_urls = await _collect_post_urls(page, profile_url, max_posts)
    if not post_urls:
        logger.warning("No se encontraron posts en %s", profile_url)
        return {"reactions": [], "comments": []}

    logger.info("Procesando %d posts...", len(post_urls))
    all_reactions: dict = {}
    all_comments: dict = {}

    for idx, post_url in enumerate(post_urls):
        logger.info("  Post [%d/%d]: %s", idx + 1, len(post_urls), post_url)

        graphql_data: list = []
        pending: set = set()

        async def _fetch(resp, _store=graphql_data, _pending=pending):
            try:
                url_lower = (resp.url or "").lower()
                if "graphql" not in url_lower and "api/v1" not in url_lower:
                    return
                data = await resp.json()
                _store.append(data)
            except Exception:
                pass

        def on_resp(resp, _fetch=_fetch, _pending=pending):
            t = asyncio.create_task(_fetch(resp))
            _pending.add(t)
            t.add_done_callback(_pending.discard)

        page.on("response", on_resp)
        try:
            await page.goto(post_url, wait_until="domcontentloaded")
            await asyncio.sleep(2)
            await dismiss_popups(page)

            # Likes
            try:
                liked_a = await page.query_selector('a[href*="/liked_by/"]')
                if not liked_a:
                    for sel in ['a:has-text("likes")', 'a:has-text("Me gusta")',
                                'div[role="button"]:has-text("likes")', 'div[role="button"]:has-text("Me gusta")']:
                        liked_a = await page.query_selector(sel)
                        if liked_a:
                            break
                if liked_a:
                    await liked_a.click()
                    await asyncio.sleep(2)
                    liker_container = await _find_scroll_container(page)
                    no_new_l = 0
                    last_l = -1
                    for _ in range(50):
                        if pending:
                            await asyncio.gather(*list(pending), return_exceptions=True)
                        for payload in list(graphql_data):
                            found = _extract_likers_from_payload(payload, username, post_url)
                            for k, v in found.items():
                                if k not in all_reactions:
                                    all_reactions[k] = v
                        await _scroll_modal(page, liker_container, 800)
                        await asyncio.sleep(0.9)
                        if len(all_reactions) == last_l:
                            no_new_l += 1
                            if no_new_l >= 6:
                                break
                        else:
                            no_new_l = 0
                        last_l = len(all_reactions)
                    try:
                        await page.keyboard.press("Escape")
                        await asyncio.sleep(0.5)
                    except Exception:
                        pass
                    logger.info("    Likes extraídos hasta ahora: %d", len(all_reactions))
            except Exception as e:
                logger.debug("    liked_by no disponible: %s", e)

            # Comments
            for _ in range(3):
                try:
                    btn = await page.query_selector(
                        'button:has-text("Cargar más comentarios"), button:has-text("Load more comments")'
                    )
                    if btn:
                        await btn.click()
                        await asyncio.sleep(2)
                    else:
                        break
                except Exception:
                    break

            for _ in range(10):
                await page.evaluate("window.scrollBy(0, 400)")
                await asyncio.sleep(1.2)

            try:
                comment_hrefs = await page.evaluate("""
                    () => {
                        const sels = [
                            'article section div div div span[dir="auto"] a',
                            'section div span[dir="auto"] a[href^="/"]',
                            'article a[href^="/"][href$="/"]',
                            'section a[href^="/"][href$="/"]',
                        ];
                        const skip = new Set(['p','reel','tv','stories','explore','accounts']);
                        const out = [];
                        for (const sel of sels) {
                            const els = document.querySelectorAll(sel);
                            if (!els.length) continue;
                            for (const el of els) {
                                const href = el.getAttribute('href') || '';
                                if (!href.startsWith('/') || !href.endsWith('/')) continue;
                                const uname = href.slice(1, -1).split('/')[0];
                                if (!uname || skip.has(uname)) continue;
                                const name = (el.textContent || '').trim();
                                let p = el.parentElement, photo = '', depth = 0;
                                while (p && depth < 5) {
                                    const img = p.querySelector('img');
                                    if (img && img.src && !img.src.startsWith('data:')) { photo = img.src; break; }
                                    p = p.parentElement; depth++;
                                }
                                out.push({ href, name, photo });
                            }
                            if (out.length) break;
                        }
                        return out;
                    }
                """) or []

                for rec in comment_hrefs:
                    href = rec.get("href") or ""
                    if not href:
                        continue
                    url_abs = f"https://www.instagram.com{href}"
                    item = build_user_item(url_abs, rec.get("name") or "", rec.get("photo") or "")
                    uname = item["username_usuario"]
                    if not uname or uname == "unknown":
                        continue
                    key = item["link_usuario"]
                    if key not in all_comments:
                        item["post_url"] = normalize_post_url(post_url)
                        item["interaction_type"] = "comment"
                        all_comments[key] = item
            except Exception as e:
                logger.debug("    Error extrayendo comentarios: %s", e)

            if pending:
                await asyncio.gather(*list(pending), return_exceptions=True)
            for payload in graphql_data:
                found = _extract_likers_from_payload(payload, username, post_url)
                for k, v in found.items():
                    if k not in all_reactions:
                        all_reactions[k] = v

        except Exception as e:
            logger.error("    Error procesando post %s: %s", post_url, e)
        finally:
            page.remove_listener("response", on_resp)
            if pending:
                await asyncio.gather(*list(pending), return_exceptions=True)

        logger.info("    Post %d: %d likes totales, %d comentarios totales",
                    idx + 1, len(all_reactions), len(all_comments))

    return {"reactions": list(all_reactions.values()), "comments": list(all_comments.values())}


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
    Ejecuta el análisis completo de un perfil de Instagram.
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
            raise RuntimeError("Sesión de Instagram inválida o expirada")

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

        username = results["profile"].get("username", "unknown")

        if scope.get("followers", False):
            logger.info("=== Extrayendo seguidores ===")
            results["followers"] = await scrap_list(page, profile_url, "followers", username, limits.get("max_followers", 0))
            if on_progress:
                on_progress("followers", {"count": len(results["followers"])})

        if scope.get("following", False):
            logger.info("=== Extrayendo seguidos ===")
            results["followed"] = await scrap_list(page, profile_url, "following", username, limits.get("max_following", 0))
            if on_progress:
                on_progress("following", {"count": len(results["followed"])})

        if scope.get("photos", False) or scope.get("reactions", False) or scope.get("comments", False):
            max_posts = limits.get("max_photos", 5)
            logger.info("=== Extrayendo likes y comentarios en posts (max %d) ===", max_posts)
            engagements = await scrap_post_engagements(page, profile_url, username, max_posts=max_posts)
            results["reactions"] = engagements.get("reactions", [])
            results["comments"] = engagements.get("comments", [])
            if on_progress:
                on_progress("engagements", {
                    "reactions": len(results["reactions"]),
                    "comments": len(results["comments"]),
                })

        await browser.close()
    return results
