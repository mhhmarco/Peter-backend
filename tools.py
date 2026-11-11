import re
import urllib.parse
from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 4) -> str:
    """Ricerca web in tempo reale tramite DuckDuckGo."""
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

def search_youtube(query: str) -> dict:
    """Estrazione dell'ID video per un player YouTube senza restrizioni di embed."""
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
                        "embed_url": f"https://www.youtube-nocookie.com/embed/{video_id}?autoplay=1",
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
    """Widget Player per Apple Music."""
    q_enc = urllib.parse.quote(query)
    return {
        "title": f"Apple Music: {query}",
        "embed_url": f"https://embed.music.apple.com/it/search?term={q_enc}",
        "source": "applemusic"
    }
