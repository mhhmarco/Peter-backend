import os
import re
import urllib.parse
from urllib.parse import urlparse, parse_qs
import httpx
import tempfile
import edge_tts
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN
from database import get_telegram_chat_id

# Read at call time so environment configuration and tests can replace the key
# without re-importing this module. The key must be a YouTube Data API v3 key.
def _youtube_api_key() -> str:
    from config import YOUTUBE_API_KEY
    return (os.getenv("YOUTUBE_API_KEY") or YOUTUBE_API_KEY or "").strip().strip('"\' ')


def _youtube_result(video_id: str, title: str, query: str, *, channel: str = "", thumbnail: str = "") -> dict:
    return {
        "title": title or query,
        "video_id": video_id,
        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?enablejsapi=1&playsinline=1&rel=0&autoplay=1",
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "source": "youtube",
        "channel": channel,
        "thumbnail": thumbnail,
    }


def _extract_youtube_id(value: str) -> str | None:
    """Extract a valid video ID from supported YouTube URL forms."""
    try:
        parsed = urlparse(value.strip())
        host = (parsed.hostname or "").lower().removeprefix("www.")
        video_id = None
        if host == "youtu.be":
            video_id = parsed.path.strip("/").split("/")[0]
        elif host in {"youtube.com", "m.youtube.com", "music.youtube.com", "youtube-nocookie.com"}:
            video_id = parse_qs(parsed.query).get("v", [None])[0]
            if not video_id:
                match = re.match(r"/(?:embed|shorts|live|v)/([^/?]+)", parsed.path)
                video_id = match.group(1) if match else None
        return video_id if video_id and re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id) else None
    except (ValueError, AttributeError):
        return None


def youtube_api_status() -> dict:
    """Return safe, non-secret diagnostics for the API-key configuration."""
    key = _youtube_api_key()
    return {"configured": bool(key), "key_type": "YouTube Data API v3" if key else None}


def _youtube_data_api_search(query: str) -> dict | None:
    """Search with YouTube Data API and select the best embeddable result.

    Search.list needs the YouTube Data API v3 enabled and a valid API key. We
    check video status before selecting, so private/non-embeddable videos are
    not chosen when the official API provides better candidates.
    """
    key = _youtube_api_key()
    if not key:
        return None
    try:
        with httpx.Client(timeout=httpx.Timeout(6.0, connect=3.0)) as client:
            response = client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={"part": "snippet", "type": "video", "maxResults": 10,
                       "q": query, "videoEmbeddable": "true", "safeSearch": "moderate", "key": key},
            )
            if response.status_code == 400 or response.status_code == 403:
                # Explicit errors are logged to Render; key itself is never logged.
                print(f“YouTube Data API search error {response.status_code}: {response.text[:400]}")
            response.raise_for_status()
            items = response.json().get("items", [])
            candidates = []
            for item in items:
                video_id = (item.get("id") or {}).get("videoId")
                snippet = item.get("snippet") or {}
                if video_id:
                    candidates.append((video_id, snippet))
            if not candidates:
                return None

            # Search.list's videoEmbeddable filter is useful but checking status
            # avoids relying on search metadata alone. videos.list costs no extra
            # quota unit beyond the request's minimum and verifies embeddability.
            status_response = client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={"part": "status", "id": ",".join(v for v, _ in candidates), "key": key},
            )
            status_response.raise_for_status()
            eligible = {entry.get("id") for entry in status_response.json().get("items", [])
                        if entry.get("status", {}).get("embeddable") is True
                        and entry.get("status", {}).get("privacyStatus") == "public"}
            for video_id, snippet in candidates:
                if video_id in eligible:
                    return _youtube_result(
                        video_id, snippet.get("title", query), query,
                        channel=snippet.get("channelTitle", ""),
                        thumbnail=(snippet.get("high") or snippet.get("medium") or snippet.get("default") or {}).get("url", ""),
                    )
    except httpx.HTTPStatusError as exc:
        print(f“YouTube API HTTP {exc.response.status_code}: {exc.response.text[:400]}")
    except Exception as exc:
        print(f“YouTube Data API non disponibile, uso ricerca alternativa: {exc}")
    return None


def _fallback_youtube_search(query: str) -> dict | None:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.videos(query, max_results=8))
        for video in results:
            url = video.get("content", "") or video.get("href", "")
            video_id = _extract_youtube_id(url)
            if not video_id:
                # DDG may return a URL with query params or a shortened URL.
                match = re.search(r"(?:v=|/embed/|/shorts/|/live/|youtu\.be/)([A-Za-z0-9_-]{11})(?:[?&/]|$)", url, re.I)
                video_id = match.group(1) if match else None
            if video_id:
                return _youtube_result(video_id, video.get("title", query), query)
    except Exception as exc:
        print(f"Errore ricerca YouTube alternativa: {exc}")
    return None


def search_youtube(query: str) -> dict:
    """Find a playable YouTube result; use official API first, DDG as fallback."""
    original_query = (query or "").strip()
    if not original_query:
        return {"title": "Ricerca YouTube", "video_id": None, "embed_url": "",
                "watch_url": "https://www.youtube.com/", "source": "youtube"}

    direct_id = _extract_youtube_id(original_query)
    if direct_id:
        return _youtube_result(direct_id, f"Video YouTube ({direct_id})", original_query)

    # Remove common Italian command framing without deleting meaningful search terms.
    search_query = re.sub(
        r"\b(?:cerca(?:mi)?|trova|riproduci|metti|fammi vedere|un video|il video|video|su youtube|youtube)\b",
        " ", original_query, flags=re.IGNORECASE,
    )
    search_query = re.sub(r"\s+", " ", search_query).strip(" :,-") or original_query

    result = _youtube_data_api_search(search_query)
    if result:
        return result
    result = _fallback_youtube_search(search_query)
    if result:
        return result
    encoded = urllib.parse.quote(search_query)
    return {"title": f"Risultati YouTube: {search_query}", "video_id": None,
            "embed_url": "", "watch_url": f"https://www.youtube.com/results?search_query={encoded}",
            "source": "youtube"}


def search_web(query: str, max_results: int = 4) -> str:
    try:
        with DDGS() as ddgs:
            results = [
                f"Fonte: {result.get('title', '')}\nSnippet: {result.get('body', '')}\nURL: {result.get('href', '')}"
                for result in ddgs.text(query, max_results=max_results)
            ]
        if results:
            return "\n---\n".join(results)
    except Exception as exc:
        print(f"Errore ricerca web: {exc}")
    return "Nessun risultato rilevante trovato."


def search_image_result(query: str) -> dict:
    """Return image URL and attribution when the image search provider supplies it."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
        if results:
            item = results[0]
            return {"image_url": item.get("image", ""), "source_url": item.get("url", "") or item.get("source", ""),
                    "title": item.get("title", query), "content": item.get("title", "")}
    except Exception as exc:
        print(f"Errore ricerca immagine: {exc}")
    return {"image_url": "", "source_url": "", "title": query, "content": ""}


def search_image(query: str) -> str:
    return search_image_result(query).get("image_url", "")


def search_apple_music(query: str) -> dict:
    q_enc = urllib.parse.quote(query)
    return {"title": f"Apple Music: {query}",
            "embed_url": f"https://embed.music.apple.com/it/search?term={q_enc}", "source": "applemusic"}


async def send_telegram_message(message_text: str) -> bool:
    token = TELEGRAM_BOT_TOKEN.strip()
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(f"https://api.telegram.org/bot{token}/sendMessage",
                                         json={"chat_id": chat_id, "text": message_text})
            return response.status_code == 200
    except Exception as exc:
        print(f"Errore invio Telegram: {exc}")
        return False


async def send_telegram_voice_note(message_text: str) -> bool:
    """Generate and send a Telegram voice note."""
    token = TELEGRAM_BOT_TOKEN.strip()
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        return False
    tmp_path = None
    try:
        tts = edge_tts.Communicate(message_text, voice="it-IT-DiegoNeural")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp:
            tmp_path = tmp.name
        await tts.save(tmp_path)
        async with httpx.AsyncClient(timeout=15.0) as client:
            with open(tmp_path, "rb") as audio_file:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendVoice",
                    data={"chat_id": chat_id},
                    files={"voice": ("voice.ogg", audio_file, "audio/ogg")},
                )
        return response.status_code == 200
    except Exception as exc:
        print(f"Errore invio nota vocale Telegram: {exc}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
