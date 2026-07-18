#!/usr/bin/env python3
"""
facebook_analyzer.py — Script standalone de análisis de Facebook.

Uso:
    python facebook_analyzer.py <url_o_username> [--headless] [--no-headless] [--max-photos N]

Requiere:
    pip install playwright pandas
    playwright install chromium
    pip install scrapling  # opcional, fallback automático si no está

El archivo facebook_storage_state.json debe estar en el mismo directorio que este script.
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
from typing import Dict, List, Optional

import pandas as pd
from playwright.async_api import async_playwright

try:
    from scrapling import Selector as ScraplingSelector
except ModuleNotFoundError:
    ScraplingSelector = None  # ponytail: graceful degradation, Playwright fallback handles it

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("fb_analyzer")

# ---------------------------------------------------------------------------
# URL Utils (inline)
# ---------------------------------------------------------------------------

def normalize_fb_url(url: str) -> str:
    """Normaliza una URL o username de Facebook a URL canónica con trailing slash."""
    url = url.strip().lstrip("@")
    if "/" not in url and "://" not in url:
        url = f"https://www.facebook.com/{url}"
    if not url.startswith(("http://", "https://")):
        url = "https://" + url.lstrip("/")
    p = urllib.parse.urlparse(url)
    host = p.netloc.lower().split(":")[0]
    fb_aliases = {"facebook.com", "www.facebook.com", "m.facebook.com", "mbasic.facebook.com", "web.facebook.com"}
    if host in fb_aliases:
        host = "www.facebook.com"
    path = (p.path or "/").replace("//", "/")
    # Keep query only for photo.php
    query = ""
    if "photo.php" in path or "/photo/" in path:
        allowed = {"fbid", "set", "id", "owner", "comment_id"}
        q = urllib.parse.parse_qs(p.query, keep_blank_values=False)
        q = {k: v for k, v in q.items() if k in allowed}
        query = urllib.parse.urlencode({k: v[-1] for k, v in q.items()}) if q else ""
    # Trailing slash for profile pages
    if not ("photo.php" in path or "/photos/" in path):
        path = path.rstrip("/") + "/"
    return urllib.parse.urlunparse(("https", host, path, "", query, ""))


def extract_fb_username(url: str) -> str:
    """Extrae username o ID de una URL de Facebook."""
    p = urllib.parse.urlparse(url)
    if "profile.php" in p.path:
        q = urllib.parse.parse_qs(p.query)
        ids = q.get("id", [])
        if ids:
            return ids[0]
    parts = [s for s in p.path.strip("/").split("/") if s]
    skip = {"friends", "friends_all", "followers", "following", "photos", "photos_by", "photos_all", "profile.php"}
    return parts[0] if parts and parts[0] not in skip else (parts[-1] if parts else "unknown")


def absolute_fb_url(href: str) -> str:
    """Convierte un href relativo en URL absoluta de Facebook."""
    if not href:
        return ""
    if href.startswith("http"):
        return href
    return urllib.parse.urljoin("https://www.facebook.com", href)


# ---------------------------------------------------------------------------
# User Item Builder (inline)
# ---------------------------------------------------------------------------

def build_user_item(href: str, name: str, photo: str = "") -> dict:
    url = normalize_fb_url(href)
    username = extract_fb_username(url)
    name = (name or "").strip() or username
    photo = (photo or "").strip()
    if photo.startswith("data:"):
        photo = ""
    return {
        "nombre_usuario": name,
        "username_usuario": username,
        "link_usuario": url,
        "foto_usuario": photo,
    }


# ---------------------------------------------------------------------------
# Session Validator
# ---------------------------------------------------------------------------

async def validate_session(page) -> bool:
    """Verifica que la sesión de Facebook esté activa. Retorna False si expiró."""
    await page.goto("https://www.facebook.com/", wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    url = page.url.lower()
    if "login.php" in url or "checkpoint" in url:
        logger.error("Sesión expirada o cuenta bloqueada (URL: %s)", page.url)
        return False
    nav = await page.query_selector('div[role="navigation"], nav')
    if not nav:
        logger.warning("No se detectó navegación — posible sesión inválida")
        return False
    logger.info("✅ Sesión de Facebook válida")
    return True


# ---------------------------------------------------------------------------
# Profile Scraper
# ---------------------------------------------------------------------------

async def get_profile_data(page, profile_url: str) -> dict:
    """Extrae nombre, username, foto y URL del perfil."""
    url = normalize_fb_url(profile_url)
    await page.goto(url, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        await asyncio.sleep(2)

    content = await page.content()
    name = "unknown"
    profile_pic = ""

    # Try Scrapling for name extraction
    if ScraplingSelector is not None and len(content) > 500:
        try:
            sel = ScraplingSelector(content=content)
            for el in list(sel.css("h1")) + list(sel.css("h2")):
                is_nav = False
                p = el.parent
                while p:
                    role = p.attrib.get("role") if p.attrib else None
                    tag = (p.tag or "").lower()
                    if role in ("banner", "navigation") or tag == "nav":
                        is_nav = True
                        break
                    p = p.parent
                if is_nav:
                    continue
                txt = ""
                if hasattr(el, "get_all_text"):
                    txt = el.get_all_text()
                if not txt and hasattr(el, "text"):
                    txt = el.text
                txt = (txt or "").strip()
                for suffix in ["\nCuenta verificada", " Cuenta verificada", " Verified account", "\nVerified account"]:
                    txt = txt.replace(suffix, "")
                if txt:
                    name = txt.strip()
                    break
        except Exception as e:
            logger.debug("Scrapling selector falló para perfil: %s", e)

    # Fallback Playwright for name
    if name == "unknown":
        try:
            el = await page.query_selector("h1")
            if el:
                name = (await el.inner_text()).strip()
        except Exception:
            pass

    # Profile picture via JS evaluate
    try:
        profile_pic = await page.evaluate(r"""
            () => {
                const imgs = Array.from(document.querySelectorAll('image, img'));
                let bestSrc = null, maxScore = -1;
                for (const img of imgs) {
                    let src = img.tagName.toLowerCase() === 'image'
                        ? (img.getAttribute('href') || img.getAttribute('xlink:href') || '')
                        : (img.currentSrc || img.src || '');
                    if (!src || src.startsWith('data:')) continue;
                    if (src.includes('rsrc.php') || src.includes('static.xx.fbcdn.net')) continue;
                    let isNav = false;
                    let p = img.parentElement;
                    while (p) {
                        const role = p.getAttribute('role');
                        const tag = p.tagName.toLowerCase();
                        if (role === 'banner' || role === 'navigation' || tag === 'nav') { isNav = true; break; }
                        p = p.parentElement;
                    }
                    if (isNav) continue;
                    let score = 0;
                    if (src.includes('scontent') || src.includes('fbcdn.net')) score += 10;
                    let isCover = false, parent = img.parentElement, depth = 0;
                    while (parent && depth < 6) {
                        const label = (parent.getAttribute('aria-label') || '').toLowerCase();
                        const cls = (parent.getAttribute('class') || '').toLowerCase();
                        if (label.includes('profile') || label.includes('perfil') || label.includes('avatar')) score += 15;
                        if (cls.includes('profile') || cls.includes('avatar')) score += 5;
                        if (label.includes('cover') || label.includes('portada') || label.includes('banner')) isCover = true;
                        if (cls.includes('cover') || cls.includes('portada') || cls.includes('banner')) isCover = true;
                        parent = parent.parentElement; depth++;
                    }
                    const selfLabel = (img.getAttribute('aria-label') || '').toLowerCase();
                    const selfAlt = (img.getAttribute('alt') || '').toLowerCase();
                    if (selfLabel.includes('profile') || selfLabel.includes('perfil') || selfAlt.includes('profile') || selfAlt.includes('perfil')) score += 15;
                    if (selfLabel.includes('cover') || selfLabel.includes('portada') || selfAlt.includes('cover') || selfAlt.includes('portada')) isCover = true;
                    const rect = img.getBoundingClientRect();
                    if (rect.width > 120 && rect.width < 320) score += 20;
                    else if (rect.width >= 50 && rect.width <= 120) score += 5;
                    if (isCover || rect.width > 400 || (rect.height > 0 && rect.width / rect.height > 1.5)) score -= 40;
                    if (score > maxScore) { maxScore = score; bestSrc = src; }
                }
                return bestSrc || '';
            }
        """)
    except Exception:
        profile_pic = ""

    # Extract numeric user ID from page source
    match = re.search(r'"userID"\s*:\s*"(\d+)"', content) or re.search(r'userID:"(\d+)"', content)
    user_id = match.group(1) if match else None

    username = url.split("facebook.com/")[-1].strip("/").split("?")[0]
    if user_id and "profile.php" in username:
        username = user_id

    return {"username": username, "nombre_completo": name, "foto_perfil": profile_pic, "url_usuario": url}


# ---------------------------------------------------------------------------
# List Scraper (friends / followers / following)
# ---------------------------------------------------------------------------

# ponytail: invalid path filter to skip non-user anchors
_INVALID_PATHS = {
    "/followers", "/following", "/friends", "/videos", "/photo", "/photos",
    "/tv", "/events", "/past_events", "/likes", "/likes_all", "/music",
    "/sports", "/map", "/movies", "/pages", "/groups", "/watch", "/reel",
    "/story", "/games", "/reviews_given", "/reviews_written",
    "/video_movies_watch", "/profile_songs", "/places_recent", "/marketplace",
}

_JS_BATCH = r"""
() => {
  const root = document.querySelector('div[role="main"]') || document;
  const anchors = Array.from(root.querySelectorAll('a[href]'));
  const out = [];
  for (const a of anchors) {
    const href = a.getAttribute('href') || '';
    if (!href || href.startsWith('javascript:') || href === '#') continue;
    const text = (a.textContent || '').trim();
    let img = '';
    const cont = a.closest('div');
    const imgel = cont
      ? (cont.querySelector('img, image') || a.querySelector('img, image'))
      : a.querySelector('img, image');
    if (imgel) img = imgel.currentSrc || imgel.src || imgel.getAttribute('xlink:href') || '';
    out.push({ href, text, img });
  }
  return out;
}
"""


def _extract_users_from_json(data, result: dict, depth: int = 0):
    """Busca nodos de usuario en JSON GraphQL de Facebook."""
    if depth > 15 or not isinstance(data, (dict, list)):
        return
    if isinstance(data, dict):
        name = data.get("name")
        url = data.get("url") or data.get("profile_url")
        if (
            isinstance(name, str) and len(name) > 1
            and isinstance(url, str)
            and "facebook.com" in url
            and "/groups/" not in url
            and "/pages/" not in url
        ):
            try:
                clean = url.split("?")[0]
                if clean not in result:
                    parsed = urllib.parse.urlparse(url)
                    q = urllib.parse.parse_qs(parsed.query)
                    final_url = url if ("id" in q or "profile.php" in clean) else clean
                    pic = ""
                    pp = data.get("profile_picture") or data.get("profilePicture")
                    if isinstance(pp, dict):
                        pic = pp.get("uri") or pp.get("url") or ""
                    result[clean] = build_user_item(final_url, name, pic)
            except Exception:
                pass
        for v in data.values():
            _extract_users_from_json(v, result, depth + 1)
    elif isinstance(data, list):
        for item in data:
            _extract_users_from_json(item, result, depth + 1)


async def scrap_list(page, profile_url: str, list_type: str) -> List[dict]:
    """
    Extrae lista de usuarios (friends_all / followers / following) usando
    scroll DOM + GraphQL interception.
    """
    suffix = {"friends_all": "friends_all", "followers": "followers", "followed": "following"}.get(list_type, list_type)
    target_url = f"{normalize_fb_url(profile_url).rstrip('/')}/{suffix}/"
    main_slug = normalize_fb_url(profile_url).rstrip("/").split("facebook.com/")[-1].strip("/")

    extracted: dict = {}
    graphql_responses: list = []
    pending: set = set()

    async def _fetch_graphql(response):
        try:
            text = await response.text()
            if "node" in text and ("Profile" in text or "User" in text or "name" in text):
                graphql_responses.append(await response.json())
        except Exception:
            pass

    def on_response(response):
        if "graphql" in response.url.lower() and response.request.method == "POST":
            t = asyncio.create_task(_fetch_graphql(response))
            pending.add(t)
            t.add_done_callback(pending.discard)

    def _process_dom(raw: list):
        for rec in raw:
            try:
                href = rec.get("href") or ""
                if not href:
                    continue
                if href.startswith("/"):
                    href = "https://www.facebook.com" + href
                elif not href.startswith("http"):
                    continue
                clean = href.split("?")[0]
                if any(pat in clean for pat in _INVALID_PATHS):
                    continue
                slug = clean.split("facebook.com/")[-1].strip("/")
                if slug in ("", "friends", "followers", "following") or slug == main_slug:
                    continue
                if clean in extracted:
                    continue
                nombre = (rec.get("text") or "").strip() or slug
                if any(nombre.lower().startswith(p) for p in ("1 amigo", "2 amigos", "1 friend", "2 friends")):
                    continue
                parsed = urllib.parse.urlparse(href)
                q = urllib.parse.parse_qs(parsed.query)
                final_url = href if ("id" in q or "profile.php" in clean) else clean
                extracted[clean] = build_user_item(final_url, nombre, rec.get("img") or "")
            except Exception:
                continue

    page.on("response", on_response)
    logger.info("Navegando a %s ...", target_url)
    await page.goto(target_url)
    await asyncio.sleep(3)

    # Early exit for locked profiles
    content = await page.content()
    if any(s in content.lower() for s in ("locked their profile", "cerró su perfil", "perfil cerrado", "restricted profile")):
        logger.warning("Perfil restringido, saltando lista '%s'", list_type)
        page.remove_listener("response", on_response)
        return []

    no_new, last_total = 0, 0
    for i in range(60):
        try:
            raw = await page.evaluate(_JS_BATCH)
            _process_dom(raw or [])
        except Exception:
            pass

        if pending:
            await asyncio.gather(*list(pending), return_exceptions=True)
        for payload in list(graphql_responses):
            _extract_users_from_json(payload, extracted)

        try:
            await page.mouse.wheel(0, 3000)
        except Exception:
            await page.evaluate("window.scrollBy(0, 3000)")
        await asyncio.sleep(0.9)

        total = len(extracted)
        if total == last_total:
            no_new += 1
            if no_new >= 4:
                logger.info("Sin nuevos usuarios en '%s'. Fin.", list_type)
                break
        else:
            no_new = 0
        last_total = total
        logger.info("  Scroll %d: %d usuarios | %d tramos GraphQL", i + 1, total, len(graphql_responses))

    page.remove_listener("response", on_response)
    if pending:
        await asyncio.gather(*list(pending), return_exceptions=True)
    for payload in graphql_responses:
        _extract_users_from_json(payload, extracted)

    return list(extracted.values())


# ---------------------------------------------------------------------------
# Photo Engagement Scraper (reacciones + comentarios en una sola pasada)
# ---------------------------------------------------------------------------

async def _open_reactions_overlay(page) -> bool:
    """Intenta abrir el modal/overlay de reacciones de la foto actual."""
    try:
        return await page.evaluate(r"""
            () => {
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style && style.visibility !== 'hidden' && style.display !== 'none'
                        && rect.width > 8 && rect.height > 8 && rect.bottom > 0 && rect.top < window.innerHeight;
                };
                const textFor = (el) => `${el.getAttribute('aria-label')||''} ${el.textContent||''}`.toLowerCase().replace(/\s+/g,' ').trim();
                const hasHint = (text, el) => {
                    if (['reacci','reaction','all reactions','todas las reacciones','like','me gusta','love','me encanta',
                         'care','haha','wow','sad','angry','others','personas más','personas mas'].some(t => text.includes(t))) return true;
                    if (/\d+/.test(text) && (el.querySelector('img,svg') || el.closest('[role="button"],[role="link"],a'))) return true;
                    const href = el.getAttribute('href')||'';
                    return href.includes('reaction/profile') || href.includes('ufi/reaction');
                };
                let best = null, bestScore = -1;
                for (const el of document.querySelectorAll('a,button,[role="button"],[role="link"],[aria-label],span,div')) {
                    if (!isVisible(el)) continue;
                    if (el.closest('div[role="article"][aria-label*="Comentario"],div[role="article"][aria-label*="Comment"]')) continue;
                    const text = textFor(el);
                    if (!hasHint(text, el)) continue;
                    let score = 0;
                    if (el.getAttribute('aria-label')) score += 3;
                    if (/\d/.test(text)) score += 5;
                    const href = el.getAttribute('href')||'';
                    if (href.includes('reaction/profile')||href.includes('ufi/reaction')) score += 15;
                    if (text.includes('todas las reacciones')||text.includes('all reactions')) score += 10;
                    if (text.includes('reaction')||text.includes('reacci')) score += 8;
                    if (text.includes('others')||text.includes('personas más')) score += 7;
                    if (text.includes('like')||text.includes('me gusta')||text.includes('love')) score += 4;
                    if (el.querySelector('img,svg')) score += 5;
                    const tag = el.tagName.toLowerCase(), role = el.getAttribute('role')||'';
                    if (tag==='a'||tag==='button'||role==='button'||role==='link') score += 3;
                    if (score > bestScore) { best = el; bestScore = score; }
                }
                if (!best) return false;
                best.click();
                return true;
            }
        """)
    except Exception:
        return False


async def _scroll_overlay(page, max_scrolls: int = 8, delta: int = 900) -> int:
    """Hace scroll dentro del overlay/modal activo."""
    scrolled = 0
    stagnant = 0
    for _ in range(max_scrolls):
        info = await page.evaluate(r"""
            (delta) => {
                const isVisible = (el) => {
                    if (!el) return false;
                    const style = window.getComputedStyle(el);
                    const rect = el.getBoundingClientRect();
                    return style && style.visibility!=='hidden' && style.display!=='none'
                        && rect.width>40 && rect.height>40 && rect.bottom>0 && rect.top<window.innerHeight;
                };
                let best = null, bestScore = -1;
                for (const el of document.querySelectorAll('*')) {
                    if (!isVisible(el)) continue;
                    const style = window.getComputedStyle(el);
                    const scrollable = el.scrollHeight > el.clientHeight + 80;
                    if (!scrollable) continue;
                    const ov = `${style.overflowY||''} ${style.overflow||''}`;
                    if (!/(auto|scroll)/.test(ov) && !el.closest('[role="dialog"],[aria-modal="true"]')) continue;
                    let score = el.scrollHeight - el.clientHeight;
                    if (el.closest('[role="dialog"],[aria-modal="true"]')) score += 100000;
                    if (style.position==='fixed'||style.position==='sticky') score += 5000;
                    const rect = el.getBoundingClientRect();
                    if (rect.width>250) score += 500;
                    if (rect.height>250) score += 500;
                    if (score > bestScore) { best = el; bestScore = score; }
                }
                const target = best || document.scrollingElement || document.documentElement;
                if (!target) return { found: false, before: 0, after: 0 };
                const before = target.scrollTop || 0;
                if (typeof target.scrollBy === 'function') target.scrollBy(0, delta);
                else target.scrollTop = before + delta;
                return { found: true, before, after: target.scrollTop || 0 };
            }
        """, delta)
        if not info.get("found"):
            break
        scrolled += 1
        if info.get("after", 0) <= info.get("before", 0) + 5:
            stagnant += 1
            if stagnant >= 2:
                break
        else:
            stagnant = 0
        await asyncio.sleep(0.6)
    return scrolled


def _build_user_from_node(node: dict) -> Optional[dict]:
    try:
        name = node.get("name")
        url = node.get("url")
        pic = ""
        pp = node.get("profile_picture")
        if isinstance(pp, dict):
            pic = pp.get("uri") or ""
        if url and name:
            clean = url.split("?")[0]
            parsed = urllib.parse.urlparse(url)
            q = urllib.parse.parse_qs(parsed.query)
            final_url = url if ("id" in q or "profile.php" in clean) else clean
            return build_user_item(final_url, name, pic)
    except Exception:
        pass
    return None


def _extract_engagements(data, reactions: dict, comments: dict):
    """Clasifica nodos GraphQL en reactores o comentadores."""
    if isinstance(data, dict):
        if "node" in data and isinstance(data["node"], dict):
            node = data["node"]
            if node.get("__typename") == "User":
                item = _build_user_from_node(node)
                if item:
                    url = item["link_usuario"]
                    if url not in reactions:
                        item["interaction_type"] = "reaction"
                        reactions[url] = item
        if data.get("__typename") == "Comment" and "author" in data:
            author = data["author"]
            if isinstance(author, dict):
                item = _build_user_from_node(author)
                if item:
                    url = item["link_usuario"]
                    if url not in comments:
                        item["interaction_type"] = "comment"
                        body = data.get("body")
                        if body and isinstance(body, dict):
                            item["comment_text"] = body.get("text")
                        comments[url] = item
        for v in data.values():
            if isinstance(v, (dict, list)):
                _extract_engagements(v, reactions, comments)
    elif isinstance(data, list):
        for item in data:
            if isinstance(item, (dict, list)):
                _extract_engagements(item, reactions, comments)


async def scrap_photo_engagements(page, profile_url: str, max_photos: int = 5) -> Dict[str, List[dict]]:
    """
    Extrae reacciones Y comentarios de fotos del perfil.
    Cada foto se procesa una sola vez: abre la ventana, intercepta GraphQL,
    abre modal de reacciones + scroll, luego scroll de comentarios en esa misma ventana.
    """
    url = normalize_fb_url(profile_url)
    photos_url = f"{url.rstrip('/')}/photos/"

    logger.info("Navegando a fotos: %s", photos_url)
    await page.goto(photos_url, wait_until="domcontentloaded")
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        await asyncio.sleep(1)

    content = await page.content()
    if any(s in content.lower() for s in ("locked their profile", "cerró su perfil", "perfil cerrado", "restricted profile")):
        logger.warning("Perfil restringido — no se pueden extraer fotos")
        return {"reactions": [], "comments": []}

    # Collect photo links
    photo_links: list = []
    if ScraplingSelector is not None and len(content) > 500:
        try:
            sel = ScraplingSelector(content=content)
            for el in sel.css('a[href*="photo.php"], a[href*="/photo/"], a[href*="/photos/"]'):
                href = el.attrib.get("href")
                if href:
                    full = absolute_fb_url(href)
                    if full not in photo_links:
                        photo_links.append(full)
                    if len(photo_links) >= max_photos:
                        break
        except Exception as e:
            logger.debug("Scrapling falló en fotos: %s", e)

    if not photo_links:
        try:
            anchors = await page.query_selector_all('a[href*="photo.php"], a[href*="/photo/"], a[href*="/photos/"]')
            for a in anchors:
                href = await a.get_attribute("href")
                if href:
                    full = absolute_fb_url(href)
                    if full not in photo_links:
                        photo_links.append(full)
                    if len(photo_links) >= max_photos:
                        break
        except Exception as e:
            logger.warning("Fallback Playwright para fotos falló: %s", e)

    if not photo_links:
        logger.warning("No se encontraron fotos en %s", photos_url)
        return {"reactions": [], "comments": []}

    logger.info("Procesando %d fotos...", len(photo_links))
    all_reactions: dict = {}
    all_comments: dict = {}

    for idx, photo_url in enumerate(photo_links):
        logger.info("  Foto [%d/%d]: %s", idx + 1, len(photo_links), photo_url)

        photo_graphql: list = []
        photo_pending: set = set()

        async def _fetch(resp, _store=photo_graphql, _pending=photo_pending):
            try:
                text = await resp.text()
                if any(k in text for k in ("reactor", "comment", "Feedback", "reaction", "Comment")):
                    _store.append(await resp.json())
            except Exception:
                pass

        def on_photo_response(resp, _fetch=_fetch, _pending=photo_pending):
            if "graphql" in resp.url.lower() and resp.request.method == "POST":
                t = asyncio.create_task(_fetch(resp))
                _pending.add(t)
                t.add_done_callback(_pending.discard)

        page.on("response", on_photo_response)
        try:
            await page.goto(photo_url)
            await asyncio.sleep(2)

            # — Reacciones: abrir modal y hacer scroll (misma ventana) —
            try:
                opened = await _open_reactions_overlay(page)
                if not opened:
                    for sel in [
                        'a[href*="reaction/profile"]', 'a[href*="ufi/reaction"]',
                        '[role="button"][aria-label*="reacci"]', '[role="button"][aria-label*="reaction"]',
                        'span[aria-label*="reacci"]', 'span[aria-label*="reaction"]',
                    ]:
                        try:
                            btn = await page.query_selector(sel)
                            if btn and await btn.is_visible():
                                await btn.click()
                                opened = True
                                break
                        except Exception:
                            pass
                if opened:
                    await asyncio.sleep(1.5)
                    scrolled = await _scroll_overlay(page)
                    logger.info("    Modal reacciones: %d scrolls", scrolled)
            except Exception as e:
                logger.debug("    Modal reacciones no disponible: %s", e)

            # — Cerrar modal, luego scroll para cargar comentarios (misma ventana) —
            try:
                await page.keyboard.press("Escape")
                await asyncio.sleep(0.5)
            except Exception:
                pass

            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await asyncio.sleep(0.6)

            # Esperar GraphQL pendiente de esta foto
            if photo_pending:
                await asyncio.gather(*list(photo_pending), return_exceptions=True)

        except Exception as e:
            logger.error("    Error procesando foto %s: %s", photo_url, e)
        finally:
            page.remove_listener("response", on_photo_response)
            if photo_pending:
                await asyncio.gather(*list(photo_pending), return_exceptions=True)

        # Parsear GraphQL capturado para esta foto
        photo_reactions: dict = {}
        photo_comments: dict = {}
        for payload in photo_graphql:
            _extract_engagements(payload, photo_reactions, photo_comments)

        # Fallback DOM para comentarios si GraphQL no los trajo
        if not photo_comments:
            try:
                dom_authors = await page.evaluate(r"""
                    () => {
                        const articles = document.querySelectorAll('div[role="article"]');
                        const out = [];
                        for (const art of articles) {
                            const links = art.querySelectorAll('a[href*="facebook.com/"], a[href^="/"]');
                            for (const a of links) {
                                const href = a.getAttribute('href') || '';
                                if (!href || href.includes('/photo') || href.includes('/groups/')) continue;
                                const txt = (a.textContent || '').trim();
                                if (!txt) continue;
                                const img = art.querySelector('img');
                                out.push({ href, text: txt, img: img ? (img.currentSrc||img.src||'') : '' });
                                break;
                            }
                        }
                        return out;
                    }
                """)
                for rec in (dom_authors or []):
                    href = rec.get("href") or ""
                    if not href:
                        continue
                    if href.startswith("/"):
                        href = "https://www.facebook.com" + href
                    clean = href.split("?")[0]
                    if clean in photo_comments:
                        continue
                    item = build_user_item(clean, (rec.get("text") or "").strip(), rec.get("img") or "")
                    item["interaction_type"] = "comment"
                    photo_comments[clean] = item
            except Exception as e:
                logger.debug("    Fallback DOM comentarios falló: %s", e)

        logger.info("    Foto %d: %d reacciones, %d comentarios", idx + 1, len(photo_reactions), len(photo_comments))
        all_reactions.update(photo_reactions)
        all_comments.update(photo_comments)

    return {"reactions": list(all_reactions.values()), "comments": list(all_comments.values())}


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------

def export_to_csv(results: dict, output_path: str) -> str:
    rows = []
    profile = results.get("profile") or {}
    if profile:
        rows.append({
            "tipo": "PERFIL",
            "username": profile.get("username", ""),
            "nombre_completo": profile.get("nombre_completo", ""),
            "url_perfil": profile.get("url_usuario", ""),
            "foto": profile.get("foto_perfil", ""),
            "interaccion": "",
            "texto_comentario": "",
        })

    def _add(user_list: List[dict], tipo: str):
        for u in user_list:
            rows.append({
                "tipo": tipo,
                "username": u.get("username_usuario", ""),
                "nombre_completo": u.get("nombre_usuario", ""),
                "url_perfil": u.get("link_usuario", ""),
                "foto": u.get("foto_usuario", ""),
                "interaccion": u.get("interaction_type", ""),
                "texto_comentario": u.get("comment_text", ""),
            })

    _add(results.get("friends", []), "AMIGO")
    _add(results.get("followers", []), "SEGUIDOR")
    _add(results.get("followed", []), "SEGUIDO")
    _add(results.get("reactions", []), "REACCION_FOTO")
    _add(results.get("comments", []), "COMENTARIO_FOTO")

    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    logger.info("CSV exportado: %s (%d filas)", output_path, len(df))
    return output_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Análisis de perfil de Facebook (standalone)")
    parser.add_argument("profile", help="URL o username del perfil (ej: juan.perez o https://facebook.com/juan.perez)")
    parser.add_argument("--headless", dest="headless", action="store_true", default=True, help="Modo headless (default)")
    parser.add_argument("--no-headless", dest="headless", action="store_false", help="Mostrar ventana del navegador")
    parser.add_argument("--max-photos", type=int, default=5, metavar="N", help="Número máximo de fotos a analizar (default: 5)")
    parser.add_argument(
        "--storage-state",
        default=str(Path(__file__).parent / "facebook_storage_state.json"),
        metavar="PATH",
        help="Ruta al storage state JSON (default: facebook_storage_state.json junto al script)",
    )
    args = parser.parse_args()

    storage_path = Path(args.storage_state)
    if not storage_path.exists():
        logger.error("No se encontró el storage state: %s", storage_path)
        logger.error("Coloca facebook_storage_state.json en el mismo directorio que este script.")
        sys.exit(1)

    profile_url = normalize_fb_url(args.profile)

    # ponytail: auto-fallback to headless if no display server available
    headless = args.headless
    if not headless and not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        logger.warning("⚠️  --no-headless requiere un servidor X ($DISPLAY). No se detectó ninguno.")
        logger.warning("   Opciones: 1) usa 'xvfb-run python3 facebook_analyzer.py ...'")
        logger.warning("             2) ejecuta desde un entorno con pantalla (escritorio/VNC)")
        logger.warning("   Continuando en modo headless automáticamente...")
        headless = True

    logger.info("Perfil objetivo: %s", profile_url)
    logger.info("Storage state: %s", storage_path)
    logger.info("Headless: %s | Max fotos: %d", headless, args.max_photos)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ],
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

        # 1. Validar sesión
        if not await validate_session(page):
            logger.error("Sesión inválida. Actualiza facebook_storage_state.json.")
            await browser.close()
            sys.exit(1)

        results = {}

        # 2. Perfil
        logger.info("=== Extrayendo perfil ===")
        results["profile"] = await get_profile_data(page, profile_url)
        username = results["profile"].get("username", "unknown")
        logger.info("Perfil: %s (%s)", results["profile"].get("nombre_completo"), username)

        # 3. Amigos
        logger.info("=== Extrayendo amigos ===")
        results["friends"] = await scrap_list(page, profile_url, "friends_all")
        logger.info("Amigos encontrados: %d", len(results["friends"]))

        # 4. Followers
        logger.info("=== Extrayendo seguidores ===")
        results["followers"] = await scrap_list(page, profile_url, "followers")
        logger.info("Seguidores encontrados: %d", len(results["followers"]))

        # 5. Following
        logger.info("=== Extrayendo seguidos ===")
        results["followed"] = await scrap_list(page, profile_url, "followed")
        logger.info("Seguidos encontrados: %d", len(results["followed"]))

        # 6. Fotos — reacciones + comentarios en una sola pasada por foto
        logger.info("=== Extrayendo reacciones y comentarios en fotos (max %d) ===", args.max_photos)
        engagements = await scrap_photo_engagements(page, profile_url, max_photos=args.max_photos)
        results["reactions"] = engagements.get("reactions", [])
        results["comments"] = engagements.get("comments", [])
        logger.info("Reacciones: %d | Comentarios: %d", len(results["reactions"]), len(results["comments"]))

        await browser.close()

    # 7. Exportar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_name = f"facebook_{username}_{timestamp}.csv"
    export_to_csv(results, csv_name)
    logger.info("✅ Análisis completado → %s", csv_name)


if __name__ == "__main__":
    asyncio.run(main())
