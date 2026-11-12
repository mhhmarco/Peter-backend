import re
import urllib.parse
import httpx
import tempfile
import os
import edge_tts
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN, YOUTUBE_API_KEY
from database import get_telegram_chat_id


def _youtube_result(video_id: str, title: str, query: str) -> dict:
    return {
        "title": title or query,
        "video_id": video_id,
        "embed_url": (
            f"https://www.youtube-nocookie.com/embed/{video_id}"
            "?enablejsapi=1&playsinline=1&rel=0"
        ),
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "source": "youtube",
    }


def _youtube_data_api_search(query: str) -> dict | None:
    """Use YouTube's official API when YOUTUBE_API_KEY is configured.

    Search results are checked for embeddability before being selected, which
    avoids many videos that would otherwise show YouTube's unavailable screen.
    """
    if not YOUTUBE_API_KEY:
        return None

    try:
        with httpx.Client(timeout=5.0) as client:
            search_response = client.get(
                "https://www.googleapis.com/youtube/v3/search",
                params={
                    "part": "snippet",
                    "type": "video",
                    "maxResults": 5,
                    "q": query,
                    "key": YOUTUBE_API_KEY,
                },
            )
            search_response.raise_for_status()
            items = search_response.json().get("items", [])
            video_ids = [
                item.get("id", {}).get("videoId")
                for item in items
                if item.get("id", {}).get("videoId")
            ]
            if not video_ids:
                return None

            status_response = client.get(
                "https://www.googleapis.com/youtube/v3/videos",
                params={
                    "part": "status",
                    "id": ",".join(video_ids),
                    "key": YOUTUBE_API_KEY,
                },
            )
            status_response.raise_for_status()
            embeddable_ids = {
                item["id"]
                for item in status_response.json().get("items", [])
                if item.get("status", {}).get("embeddable") is True
            }

            for item in items:
                video_id = item.get("id", {}).get("videoId")
                if video_id in embeddable_ids:
                    title = item.get("snippet", {}).get("title", query)
                    return _youtube_result(video_id, title, query)
    except Exception as e:
        print(f"YouTube Data API non disponibile, uso ricerca alternativa: {e}")

    return None


def search_youtube(query: str) -> dict:
    """Find a video and return embed and watch links.

    If configured, the official YouTube Data API is preferred and results are
    filtered to videos that permit embedding. DuckDuckGo is the no-key fallback.
    """
    query = (query or "").strip()
    if not query:
        return {
            "title": "Ricerca YouTube",
            "video_id": None,
            "embed_url": "",
            "watch_url": "https://www.youtube.com/",
            "source": "youtube",
        }

    # Accept direct YouTube video links before performing a search.
    direct_match = re.search(
        r"(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:embed/|shorts/|live/|watch\\?.*?v=))([A-Za-z0-9_-]{11})",
        query,
        re.IGNORECASE,
    )
    if direct_match:
        video_id = direct_match.group(1)
        return _youtube_result(video_id, f"Video YouTube ({video_id})", query)

    clean_query = re.sub(r"\b(video|metti|canzone|riproduci|su youtube)\b", "", query, flags=re.IGNORECASE).strip()
    search_query = clean_query or query

    api_result = _youtube_data_api_search(search_query)
    if api_result:
        return api_result

    try:
        with DDGS() as ddgs:
            for video in ddgs.videos(search_query, max_results=8):
                url = video.get("content", "") or video.get("href", "")
                match = re.search(
                    r"(?:v=|/embed/|/shorts/|youtu\.be/)([A-Za-z0-9_-]{11})",
                    url,
                    re.IGNORECASE,
                )
                if match:
                    return _youtube_result(
                        match.group(1), video.get("title", query), query
                    )
    except Exception as e:
        print(f"Errore ricerca YouTube: {e}")

    # A search page is a useful fallback, but not a playable video embed.
    encoded = urllib.parse.quote(search_query)
    return {
        "title": f"Risultati YouTube: {search_query}",
        "video_id": None,
        "embed_url": "",
        "watch_url": f"https://www.youtube.com/results?search_query={encoded}",
        "source": "youtube",
    }


def search_web(query: str, max_results: int = 4) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=max_results):
                results.append(
                    f"Fonte: {result.get('title', '')}\n"
                    f"Snippet: {result.get('body', '')}\n"
                    f"URL: {result.get('href', '')}"
                )
        if results:
            return "\n---\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web: {e}")
    return "Nessun risultato rilevante trovato."


def search_image(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
            if results and "image" in results[0]:
                return results[0]["image"]
    except Exception as e:
        print(f"Errore ricerca immagine: {e}")
    return ""


def search_apple_music(query: str) -> dict:
    q_enc = urllib.parse.quote(query)
    return {
        "title": f"Apple Music: {query}",
        "embed_url": f"https://embed.music.apple.com/it/search?term={q_enc}",
        "source": "applemusic",
    }


async def send_telegram_message(message_text: str) -> bool:
    token = TELEGRAM_BOT_TOKEN.strip()
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": message_text})
            return response.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
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

        url = f"https://api.telegram.org/bot{token}/sendVoice"
        async with httpx.AsyncClient(timeout=15.0) as client:
            with open(tmp_path, "rb") as audio_file:
                response = await client.post(
                    url,
                    data={"chat_id": chat_id},
                    files={"voice": ("voice.ogg", audio_file, "audio/ogg")},
                )
        return response.status_code == 200
    except Exception as e:
        print(f"Errore invio nota vocale Telegram: {e}")
        return False
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
