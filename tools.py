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
                results.append(f"Fonte: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}")
        if results:
            return "\n---\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web DDG: {e}")
    return ""

def search_image(query: str) -> str:
    """Cerca l'URL di un'immagine rilevante sul web."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, max_results=1))
            if results and "image" in results[0]:
                return results[0]["image"]
    except Exception as e:
        print(f"Errore ricerca immagine: {e}")
    return ""

def search_youtube(query: str) -> dict:
    """Estrae l'ID esatto del video YouTube per il player embed."""
    try:
        with DDGS() as ddgs:
            res = list(ddgs.videos(query, max_results=3))
            for v in res:
                url = v.get("content", "")
                match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
                if match:
                    video_id = match.group(1)
                    return {
                        "title": v.get("title", query),
                        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1&enablejsapi=1",
                        "source": "youtube"
                    }
    except Exception as e:
        print(f"Errore ricerca YouTube: {e}")
    
    return {
        "title": f"Ricerca YouTube: {query}",
        "embed_url": "",
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
    """Invia un messaggio reale sulla chat Telegram dell'utente."""
    token = TELEGRAM_BOT_TOKEN.strip()
    chat_id = get_telegram_chat_id()
    if not token or not chat_id:
        print("Manca Token o Chat ID di Telegram")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(url, json={"chat_id": chat_id, "text": message_text})
            return res.status_code == 200
    except Exception as e:
        print(f"Errore invio Telegram: {e}")
        return False
