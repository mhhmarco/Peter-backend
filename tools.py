import re
import urllib.parse
import httpx
from duckduckgo_search import DDGS
from config import TELEGRAM_BOT_TOKEN
from database import get_telegram_chat_id

def search_web(query: str, max_results: int = 4) -> str:
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Fonte: {r.get('title', '')}\nSnippet: {r.get('body', '')}\nURL: {r.get('href', '')}")
        if results:
            return "\n---\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web DDG: {e}")
    return "Nessun risultato rilevante trovato sul web."

def search_image(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
            if results and "image" in results[0]:
                return results[0]["image"]
    except Exception as e:
        print(f"Errore ricerca immagine: {e}")
    return ""

def search_youtube(query: str) -> dict:
    """Estrae l'ID esatto del video YouTube per evitare il blocco 'Video unavailable'."""
    clean_query = query.replace("video", "").replace("gatti", "cats").strip()
    try:
        with DDGS() as ddgs:
            res = list(ddgs.videos(clean_query if clean_query else query, max_results=5))
            for v in res:
                url = v.get("content", "") or v.get("href", "")
                # Regex rigorosa per estrarre solo ID validi a 11 caratteri senza trattini iniziali spuri
                match = re.search(r'(?:v=|\/embed\/|\/watch\?v=|\/youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
                if match:
                    video_id = match.group(1)
                    if not video_id.startswith("-"):
                        return {
                            "title": v.get("title", query),
                            "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1&rel=0",
                            "watch_url": f"https://www.youtube.com/watch?v={video_id}",
                            "source": "youtube"
                        }
    except Exception as e:
        print(f"Errore ricerca YouTube DDG: {e}")
    
    # Fallback embed di ricerca se la ricerca diretta fallisce
    encoded = urllib.parse.quote(query)
    return {
        "title": f"Ricerca YouTube: {query}",
        "embed_url": f"https://www.youtube.com/embed?listType=search&list={encoded}",
        "watch_url": f"https://www.youtube.com/results?search_query={encoded}",
        "source": "youtube"
    }

def search_apple_music(query: str) -> dict:
    q_enc = urllib.parse.quote(query)
    return {
        "title": f"Apple Music: {query}",
        "embed_url": f"https://embed.music.apple.com/it/search?term={q_enc}",
        "source": "applemusic"
    }

async def send_telegram_message(message_text: str) -> bool:
    token = TELEGRAM_BOT_TOKEN.strip()
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(url, json={"chat_id": chat_id, "text": message_text})
            return res.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
        return False
