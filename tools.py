import re
import httpx
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY
from database import get_telegram_chat_id


def youtube_api_status() -> dict:
    return {
        "configured": bool(YOUTUBE_API_KEY),
        "mode": "youtube_data_api_v3" if YOUTUBE_API_KEY else "html_fallback"
    }


def search_web(query: str, max_results: int = 4) -> str:
    """Ricerca web sintetica e pulita per fornire dati reali agli LLM e all'HUD."""
    if not query:
        return ""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="it-it", safesearch="moderate", max_results=max_results))
            if not results:
                return ""
            lines = []
            for r in results:
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()
                href = r.get("href", "").strip()
                lines.append(f"- {title}: {body} ({href})")
            return "\n".join(lines)
    except Exception as e:
        print(f"Errore search_web: {e}")
        return ""


def search_image_result(query: str, max_results: int = 5) -> dict:
    """Restituisce immagine principale, thumbnail di riserva, fonte e galleria per il Visual HUD."""
    clean_q = re.sub(r'^(mostrami|fammi vedere|cerca|trova|foto di|immagine di|immagini di)\s+', '', query.strip(), flags=re.IGNORECASE).strip()
    if not clean_q:
        clean_q = query.strip()

    items = []
    # 1. Ricerca primaria DuckDuckGo Images
    try:
        with DDGS() as ddgs:
            raw_images = list(ddgs.images(clean_q, region="it-it", safesearch="moderate", max_results=max_results))
            for r in raw_images:
                img_url = r.get("image") or ""
                thumb_url = r.get("thumbnail") or img_url
                if img_url.startswith("http"):
                    items.append({
                        "title": r.get("title") or clean_q,
                        "image_url": img_url,
                        "thumbnail_url": thumb_url,
                        "source_url": r.get("url") or ""
                    })
    except Exception as e:
        print(f"Errore DDGS images: {e}")

    # 2. Fallback automatico su Wikimedia Commons API se DuckDuckGo viene limitato su Render
    if not items:
        try:
            with httpx.Client(timeout=6.0, headers={"User-Agent": "PeterOS/1.0"}) as client:
                resp = client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": f"filetype:bitmap {clean_q}",
                        "gsrnamespace": 6,
                        "gsrlimit": max_results,
                        "prop": "imageinfo",
                        "iiprop": "url|extmetadata",
                        "iiurlwidth": 800,
                        "format": "json"
                    }
                )
                if resp.status_code == 200:
                    pages = resp.json().get("query", {}).get("pages", {})
                    for page in pages.values():
                        info = (page.get("imageinfo") or [{}])[0]
                        thumb = info.get("thumburl") or info.get("url")
                        full = info.get("url") or thumb
                        if full:
                            items.append({
                                "title": page.get("title", "").replace("File:", ""),
                                "image_url": thumb or full,
                                "thumbnail_url": thumb or full,
                                "source_url": info.get("descriptionurl") or ""
                            })
        except Exception as e:
            print(f"Errore Wikimedia fallback: {e}")

    if not items:
        return {"title": clean_q, "image_url": None, "thumbnail_url": None, "source_url": "", "images": []}

    first = items[0]
    return {
        "title": first["title"],
        "image_url": first["image_url"],
        "thumbnail_url": first["thumbnail_url"],
        "source_url": first["source_url"],
        "images": items
    }


def search_image(query: str) -> str | None:
    """Compatibilità retroattiva: restituisce l'URL principale dell'immagine."""
    res = search_image_result(query, max_results=3)
    return res.get("image_url")


def search_youtube(query: str) -> dict | None:
    """Cerca un video YouTube incorporabile (via API v3 se presente, altrimenti fallback diretto)."""
    clean_q = re.sub(r'^(cerca su youtube|riproduci|metti|video di|su youtube)\s+', '', query.strip(), flags=re.IGNORECASE).strip() or query.strip()

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

    # Fallback senza API key: cerca su YouTube HTML e prende il primo videoId valido
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
    """Cerca un brano su iTunes / Apple Music e restituisce il player embed."""
    try:
        with httpx.Client(timeout=6.0) as client:
            res = client.get("https://itunes.apple.com/search", params={"term": query, "media": "music", "limit": 1, "country": "IT"})
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
