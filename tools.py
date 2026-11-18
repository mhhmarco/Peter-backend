import re
import httpx
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY
from database import get_telegram_chat_id

HEADERS = {
    "User-Agent": "PeterOS-PersonalAssistant/1.1 (https://github.com/mhhmarco/Peter-backend; contact@peteros.local)",
    "Accept": "application/json"
}


def youtube_api_status() -> dict:
    return {
        "configured": bool(YOUTUBE_API_KEY),
        "mode": "youtube_data_api_v3" if YOUTUBE_API_KEY else "oembed_verified_search"
    }


def _clean_entity_query(query: str) -> str:
    q = (query or "").strip().rstrip("?.!")
    q = re.sub(
        r'^(chi è|chi era|chi sono|cos\'è|cosa è|cosa sono|parlami di|dimmi di|info su|informazioni su|mostrami|fammi vedere|cerca|trova|foto di|immagine di|immagini di)\s+(un|una|uno|il|lo|la|i|gli|le|l\')?\s*',
        '',
        q,
        flags=re.IGNORECASE
    ).strip()
    return q or (query or "").strip()


def _is_relevant_image(query: str, title: str) -> bool:
    """Verifica che il titolo dell'immagine condivida almeno una parola chiave significativa con la query."""
    stop = {"di", "da", "il", "lo", "la", "i", "gli", "le", "un", "una", "uno", "per", "con", "su", "che", "del", "della", "the", "of", "and", "in"}
    q_tokens = [w for w in re.findall(r'[a-z0-9àèéìòù]{3,}', query.lower()) if w not in stop]
    if not q_tokens:
        return True
    t_lower = (title or "").lower()
    return any(tok in t_lower for tok in q_tokens)


def search_web(query: str, max_results: int = 4) -> str:
    """Ricerca informazioni reali: Wikipedia IT exact match + DuckDuckGo."""
    if not query:
        return ""
    entity = _clean_entity_query(query)
    lines = []

    with httpx.Client(timeout=6.0, headers=HEADERS, follow_redirects=True) as client:
        try:
            open_res = client.get(
                "https://it.wikipedia.org/w/api.php",
                params={
                    "action": "opensearch",
                    "search": entity,
                    "limit": 2,
                    "namespace": 0,
                    "format": "json"
                }
            )
            titles = open_res.json()[1] if open_res.status_code == 200 else []
            if titles:
                ext_res = client.get(
                    "https://it.wikipedia.org/w/api.php",
                    params={
                        "action": "query",
                        "titles": "|".join(titles),
                        "prop": "extracts",
                        "exintro": True,
                        "explaintext": True,
                        "exsentences": 5,
                        "redirects": 1,
                        "format": "json"
                    }
                )
                if ext_res.status_code == 200:
                    pages = ext_res.json().get("query", {}).get("pages", {})
                    for p in pages.values():
                        title = p.get("title", "")
                        extract = (p.get("extract") or "").strip()
                        if extract and "può riferirsi a:" not in extract.lower():
                            lines.append(f"- [Wikipedia] {title}: {extract}")
        except Exception as e:
            print(f"Errore Wikipedia exact text: {e}")

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(entity, region="it-it", safesearch="moderate", max_results=max_results))
            for r in results:
                title = r.get("title", "").strip()
                body = r.get("body", "").strip()
                if title and body:
                    lines.append(f"- {title}: {body}")
    except Exception as e:
        print(f"Errore DDGS text: {e}")

    return "\n".join(lines[:max_results])


def search_image_result(query: str, max_results: int = 5) -> dict:
    """Ricerca immagini coerenti e verificate (Wikipedia IT/EN, Wikimedia Commons, Openverse, DDGS)."""
    clean_q = _clean_entity_query(query)
    items = []
    seen_urls = set()

    def add_item(title: str, img_url: str, thumb_url: str = "", source_url: str = "", enforce_relevance: bool = True):
        if not img_url or not img_url.startswith("http"):
            return
        if img_url in seen_urls or img_url.lower().endswith(".svg"):
            return
        if enforce_relevance and not _is_relevant_image(clean_q, title):
            return
        seen_urls.add(img_url)
        items.append({
            "title": title or clean_q,
            "image_url": img_url,
            "thumbnail_url": thumb_url or img_url,
            "source_url": source_url
        })

    with httpx.Client(timeout=6.0, headers=HEADERS, follow_redirects=True) as client:
        # 1. Wikipedia IT & EN (titolo pagina esatto con opensearch + pageimages)
        for lang in ("it", "en"):
            if len(items) >= max_results:
                break
            try:
                open_res = client.get(
                    f"https://{lang}.wikipedia.org/w/api.php",
                    params={"action": "opensearch", "search": clean_q, "limit": 3, "namespace": 0, "format": "json"}
                )
                titles = open_res.json()[1] if open_res.status_code == 200 else []
                if titles:
                    resp = client.get(
                        f"https://{lang}.wikipedia.org/w/api.php",
                        params={
                            "action": "query",
                            "titles": "|".join(titles),
                            "prop": "pageimages|info",
                            "piprop": "thumbnail|original",
                            "pithumbsize": 800,
                            "inprop": "url",
                            "redirects": 1,
                            "format": "json"
                        }
                    )
                    if resp.status_code == 200:
                        pages = resp.json().get("query", {}).get("pages", {})
                        for p in pages.values():
                            thumb = (p.get("thumbnail") or {}).get("source")
                            orig = (p.get("original") or {}).get("source")
                            best = thumb or orig
                            if best:
                                add_item(
                                    title=p.get("title", clean_q),
                                    img_url=best,
                                    thumb_url=thumb or best,
                                    source_url=p.get("fullurl", ""),
                                    enforce_relevance=False
                                )
            except Exception as e:
                print(f"Errore Wikipedia ({lang}) images: {e}")

        # 2. Wikimedia Commons con filtro rilevanza sul nome file
        if len(items) < max_results:
            try:
                resp = client.get(
                    "https://commons.wikimedia.org/w/api.php",
                    params={
                        "action": "query",
                        "generator": "search",
                        "gsrsearch": clean_q,
                        "gsrnamespace": 6,
                        "gsrlimit": max_results * 2,
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
                        clean_title = p.get("title", clean_q).replace("File:", "").rsplit(".", 1)[0]
                        if thumb or full:
                            add_item(
                                title=clean_title,
                                img_url=thumb or full,
                                thumb_url=thumb or full,
                                source_url=info.get("descriptionurl", ""),
                                enforce_relevance=True
                            )
            except Exception as e:
                print(f"Errore Wikimedia Commons: {e}")

        # 3. Openverse API
        if len(items) < max_results:
            try:
                resp = client.get(
                    "https://api.openverse.org/v1/images/",
                    params={"q": clean_q, "page_size": max_results * 2}
                )
                if resp.status_code == 200:
                    for r in resp.json().get("results", []):
                        add_item(
                            title=r.get("title") or clean_q,
                            img_url=r.get("url") or "",
                            thumb_url=r.get("thumbnail") or r.get("url") or "",
                            source_url=r.get("foreign_landing_url") or "",
                            enforce_relevance=True
                        )
            except Exception as e:
                print(f"Errore Openverse images: {e}")

    # 4. DuckDuckGo Images fallback
    if not items:
        try:
            with DDGS() as ddgs:
                for r in ddgs.images(clean_q, region="it-it", safesearch="moderate", max_results=max_results):
                    add_item(
                        title=r.get("title") or clean_q,
                        img_url=r.get("image") or "",
                        thumb_url=r.get("thumbnail") or r.get("image") or "",
                        source_url=r.get("url") or "",
                        enforce_relevance=False
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


def _verify_youtube_oembed(client: httpx.Client, video_id: str) -> dict | None:
    """Verifica tramite YouTube oEmbed ufficiale che il video esista e sia incorporabile."""
    watch_url = f"https://www.youtube.com/watch?v={video_id}"
    try:
        res = client.get("https://www.youtube.com/oembed", params={"url": watch_url, "format": "json"})
        if res.status_code == 200:
            data = res.json()
            return {
                "source": "youtube",
                "video_id": video_id,
                "title": data.get("title") or "YouTube Video",
                "author": data.get("author_name") or "",
                "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?rel=0&playsinline=1",
                "watch_url": watch_url
            }
    except Exception:
        pass
    return None


def search_youtube(query: str) -> dict | None:
    """Cerca un video YouTube reale e lo valida via oEmbed prima di restituirlo all'HUD."""
    clean_q = re.sub(
        r'^(mostrami|fammi vedere|cerca su youtube|cerca|riproduci|metti|ascolta|video di|una canzone di|un brano di|su youtube)\s+',
        '',
        (query or "").strip(),
        flags=re.IGNORECASE
    ).strip()
    clean_q = re.sub(r'\s+(su youtube|da youtube)$', '', clean_q, flags=re.IGNORECASE).strip() or (query or "").strip()

    with httpx.Client(timeout=8.0, headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/126.0 Safari/537.36"}, follow_redirects=True) as client:
        # 1. YouTube Data API v3 se configurata
        if YOUTUBE_API_KEY:
            try:
                res = client.get(
                    "https://www.googleapis.com/youtube/v3/search",
                    params={
                        "part": "snippet",
                        "q": clean_q,
                        "type": "video",
                        "videoEmbeddable": "true",
                        "maxResults": 3,
                        "key": YOUTUBE_API_KEY
                    }
                )
                if res.status_code == 200:
                    for item in res.json().get("items", []):
                        vid = item["id"]["videoId"]
                        verified = _verify_youtube_oembed(client, vid)
                        if verified:
                            return verified
            except Exception as e:
                print(f"Errore YouTube API: {e}")

        # 2. Ricerca diretta HTML YouTube + verifica oEmbed sui primi candidati
        candidate_ids = []
        try:
            res = client.get("https://www.youtube.com/results", params={"search_query": clean_q})
            if res.status_code == 200:
                found = re.findall(r'"videoId":"([A-Za-z0-9_-]{11})"', res.text)
                for vid in found:
                    if vid not in candidate_ids:
                        candidate_ids.append(vid)
                    if len(candidate_ids) >= 5:
                        break
        except Exception as e:
            print(f"Errore YouTube HTML search: {e}")

        # 3. Fallback DuckDuckGo site:youtube.com/watch se YouTube HTML blocca
        if not candidate_ids:
            try:
                with DDGS() as ddgs:
                    for r in ddgs.text(f"site:youtube.com/watch {clean_q}", max_results=5):
                        href = r.get("href", "")
                        m = re.search(r'[?&]v=([A-Za-z0-9_-]{11})', href)
                        if m and m.group(1) not in candidate_ids:
                            candidate_ids.append(m.group(1))
            except Exception as e:
                print(f"Errore DDGS YouTube fallback: {e}")

        for vid in candidate_ids:
            verified = _verify_youtube_oembed(client, vid)
            if verified:
                return verified

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
