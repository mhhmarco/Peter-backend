import re
import httpx
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY
from database import get_telegram_chat_id

HEADERS = {
    "User-Agent": "PeterOS-PersonalAssistant/1.0 (https://github.com/mhhmarco/Peter-backend; contact@peteros.local)",
    "Accept": "application/json"
}


def youtube_api_status() -> dict:
    return {
        "configured": bool(YOUTUBE_API_KEY),
        "mode": "youtube_data_api_v3" if YOUTUBE_API_KEY else "html_fallback"
    }


def search_web(query: str, max_results: int = 4) -> str:
    """Ricerca informazioni reali: usa Wikipedia IT come fonte primaria affidabile su Render + DuckDuckGo."""
    if not query:
        return ""
    lines = []

    # 1. Riassunto rapido da Wikipedia IT (veloce e mai bloccato su Render)
    try:
        with httpx.Client(timeout=5.0, headers=HEADERS) as client:
            res = client.get(
                "https://it.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "generator": "search",
                    "gsrsearch": query,
                    "gsrlimit": 2,
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "exsentences": 3,
                    "format": "json"
                }
            )
            if res.status_code == 200:
                pages = res.json().get("query", {}).get("pages", {})
                for p in pages.values():
                    title = p.get("title", "")
                    extract = (p.get("extract") or "").strip()
                    if extract:
                        lines.append(f"- {title}: {extract}")
    except Exception as e:
        print(f"Errore Wikipedia text: {e}")

    # 2. Integra con DuckDuckGo se servono risultati web aggiuntivi
    if len(lines) < 2:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, region="it-it", safesearch="moderate", max_results=max_results))
                for r in results:
                    title = r.get("title", "").strip()
                    body = r.get("body", "").strip()
                    if title and body:
                        lines.append(f"- {title}: {body}")
        except Exception as e:
            print(f"Errore DDGS text: {e}")

    return "\n".join(lines[:max_results])


def search_image_result(query: str, max_results: int = 5) -> dict:
    """
    Recupera immagini reali garantite anche da IP cloud (Render) usando in cascata:
    1. Wikipedia PageImages (IT + EN)
    2. Wikimedia Commons API
    3. Openverse API (archivio globale immagini libero senza API key)
    4. DuckDuckGo Images
    """
    clean_q = re.sub(
        r'^(mostrami|fammi vedere|cerca|trova|foto di|immagine di|immagini di)\s+(un|una|uno|il|lo|la|i|gli|le)?\s*',
        '',
        query.strip(),
        flags=re.IGNORECASE
    ).strip() or query.strip()

    items = []
    seen_urls = set()

    def add_item(title: str, img_url: str, thumb_url: str = "", source_url: str = ""):
        if not img_url or not img_url.startswith("http"):
            return
        if img_url in seen_urls or img_url.lower().endswith(".svg"):
            return
        seen_urls.add(img_url)
        items.append({
            "title": title or clean_q,
            "image_url": img_url,
            "thumbnail_url": thumb_url or img_url,
            "source_url": source_url
        })

    with httpx.Client(timeout=6.0, headers=HEADERS, follow_redirects=True) as client:
        # 1. Wikipedia IT & EN PageImages (funziona sempre su Render ed è istantaneo)
        for lang in ("it", "en"):
            if len(items) >= max_results:
                break
            try:
                resp = client.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": clean_q,
                        "gsrlimit": max_results,
                        "prop": "pageimages|info",
                        "piprop": "thumbnail|original",
                        "pithumbsize": 800,
                        "inprop": "url",
                        "format": "json"
                    }
                )
                if resp.status_code == 200:
                    pages = resp.json().get("query", {}).get("pages", {})
                    sorted_pages = sorted(pages.values(), key=lambda x: x.get("index", 99))
                    for p in sorted_pages:
                        thumb = (p.get("thumbnail") or {}).get("source")
                        orig = (p.get("original") or {}).get("source")
                        best = thumb or orig
                        if best:
                            add_item(
                                title=p.get("title", clean_q),
                                img_url=best,
                                thumb_url=thumb or best,
                                source_url=p.get("fullurl", "")
                            )
            except Exception as e:
                print(f"Errore Wikipedia ({lang}) images: {e}")

        # 2. Wikimedia Commons (ottimo per oggetti comuni come lavastoviglie, auto, monumenti)
        if len(items) < max_results:
            try:
                resp = client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": clean_q,
                        "gsrnamespace": 6,
                        "gsrlimit": max_results,
                        "prop": "imageinfo",
                        "iiprop": "url",
                        "iiurlwidth": 800,
                        "format": "json"
                    }
                )
                if resp.status_code == 200:
                    pages = resp.json().get("query", {}).get("pages", {})
                    for p in pages.values():
                        info = (p.get("imageinfo") or [{}])[0]
                        thumb = info.get("thumburl")
                        full = info.get("url")
                        if thumb or full:
                            add_item(
                                title=p.get("title", clean_q).replace("File:", "").rsplit(".", 1)[0],
                                img_url=thumb or full,
                                thumb_url=thumb or full,
                                source_url=info.get("descriptionurl", "")
                            )
            except Exception as e:
                print(f"Errore Wikimedia Commons: {e}")

        # 3. Openverse API (ricerca immagini libera con milioni di foto reali)
        if len(items) < max_results:
            try:
                resp = client.get(
                    "https://api.openverse.org/v1/images/",
                    params={"q": clean_q, "page_size": max_results}
                )
                if resp.status_code == 200:
                    for r in resp.json().get("results", []):
                        add_item(
                            title=r.get("title") or clean_q,
                            img_url=r.get("url") or "",
                            thumb_url=r.get("thumbnail") or r.get("url") or "",
                            source_url=r.get("foreign_landing_url") or ""
                        )
            except Exception as e:
                print(f"Errore Openverse images: {e}")

    # 4. DuckDuckGo Images come ultimo fallback
    if not items:
        try:
            with DDGS() as ddgs:
                for r in ddgs.images(clean_q, region="it-it", safesearch="moderate", max_results=max_results):
                    add_item(
                        title=r.get("title") or clean_q,
                        img_url=r.get("image") or "",
                        thumb_url=r.get("thumbnail") or r.get("image") or "",
                        source_url=r.get("url") or ""
                    )
        except Exception as e:
            print(f"Errore DDGS images: {e}")

    if not items:
        return {"title": clean_q, "image_url": None, "thumbnail_url": None, "source_url": "", "images": []}

    first = items[0]
    return {
        "title": first["title"],
        "image_url": first["image_url"],
        "thumbnail_url": first["thumbnail_url"],
        "source_url": first["source_url"],
        "images": items[:max_results]
    }


def search_image(query: str) -> str | None:
    res = search_image_result(query, max_results=3)
    return res.get("image_url")


def search_youtube(query: str) -> dict | None:
    """Cerca un video YouTube incorporabile (via API v3 se presente, altrimenti fallback diretto)."""
    clean_q = re.sub(
        r'^(cerca su youtube|riproduci|metti|video di|su youtube)\s+',
        '',
        query.strip(),
        flags=re.IGNORECASE
    ).strip() or query.strip()

    if YOUTUBE_API_KEY:
        try:
            with httpx.Client(timeout=8.0) as client:
                res = client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": clean_q,
                        "type": "video",
                        "videoEmbeddable": "true",
                        "maxResults": 1,
                        "key": YOUTUBE_API_KEY
                    }
                )
                if res.status_code == 200:
                    items = res.json().get("items", [])
                    if items:
                        vid = items[0]["id"]["videoId"]
                        title = items[0]["snippet"]["title"]
                        return {
                            "source": "youtube",
                            "video_id": vid,
                            "title": title,
                            "embed_url": f"https://www.youtube-nocookie.com/embed/{vid}",
                            "watch_url": f"https://www.youtube.com/watch?v={vid}"
                        }
        except Exception as e:
            print(f"Errore YouTube API: {e}")

    try:
        with httpx.Client(timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
            res = client.get("https://www.youtube.com/results", params={"search_query": clean_q})
            if res.status_code == 200:
                match = re.search(r'"videoId":"([A-Za-z0-9_-]{11})"', res.text)
                if match:
                    vid = match.group(1)
                    return {
                        "source": "youtube",
                        "video_id": vid,
                        "title": clean_q,
                        "embed_url": f"https://www.youtube-nocookie.com/embed/{vid}",
                        "watch_url": f"https://www.youtube.com/watch?v={vid}"
                    }
    except Exception as e:
        print(f"Errore YouTube fallback: {e}")

    return None


def search_apple_music(query: str) -> dict | None:
    try:
        with httpx.Client(timeout=6.0) as client:
            res = client.get(
                "https://itunes.apple.com/search",
                params={"term": query, "media": "music", "limit": 1, "country": "IT"}
            )
            if res.status_code == 200:
                results = res.json().get("results", [])
                if results:
                    track = results[0]
                    track_view = track.get("trackViewUrl", "")
                    embed_url = track_view.replace("https://music.apple.com", "https://embed.music.apple.com") if track_view else ""
                    return {
                        "source": "apple_music",
                        "title": f"{track.get('trackName', query)} - {track.get('artistName', '')}",
                        "embed_url": embed_url,
                        "preview_url": track.get("previewUrl", "")
                    }
    except Exception as e:
        print(f"Errore Apple Music: {e}")
    return None


async def send_telegram_message(text: str) -> bool:
    chat_id = get_telegram_chat_id()
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={"chat_id": chat_id, "text": text}
            )
            return res.status_code == 200
    except Exception as e:
        print(f"Errore Telegram send: {e}")
        return False


async def send_telegram_voice_note(text: str) -> bool:
    chat_id = get_telegram_chat_id()
    if not TELEGRAM_BOT_TOKEN or not chat_id:
        return False
    try:
        import edge_tts
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp_path = tmp.name
        await edge_tts.Communicate(text, voice="it-IT-DiegoNeural").save(tmp_path)
        async with httpx.AsyncClient(timeout=15.0) as client:
            with open(tmp_path, "rb") as f:
                res = await client.post(
                    f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVoice",
                    data={"chat_id": chat_id},
                    files={"voice": ("peter_voice.mp3", f, "audio/mpeg")}
                )
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return res.status_code == 200
    except Exception as e:
        print(f"Errore Telegram voice: {e}")
        return False
