import urllib.parse
from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 5) -> str:
    """Ricerca web live via DuckDuckGo."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Fonte: {r['title']}\nSnippet: {r['body']}\nURL: {r['href']}\n")
        if results:
            return "\n---\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web DDG: {e}")
    return ""

def search_youtube(query: str) -> dict:
    """Restituisce il player iFrame embed per qualsiasi video o ricerca YouTube."""
    q_enc = urllib.parse.quote(query)
    try:
        with DDGS() as ddgs:
            res = list(ddgs.videos(query, max_results=1))
            if res and "content" in res[0]:
                url = res[0]["content"]
                v_id = ""
                if "v=" in url:
                    v_id = url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in url:
                    v_id = url.split("youtu.be/")[1].split("?")[0]
                if v_id:
                    return {
                        "title": res[0].get("title", query),
                        "embed_url": f"https://www.youtube.com/embed/{v_id}?autoplay=1",
                        "source": "youtube"
                    }
    except Exception as e:
        print(f"Errore ricerca YouTube DDG: {e}")
    
    # Fallback garantito: YouTube List Search Embed
    return {
        "title": f"Ricerca YouTube: {query}",
        "embed_url": f"https://www.youtube.com/embed?listType=search&list={q_enc}",
        "source": "youtube"
    }

def search_apple_music(query: str) -> dict:
    """Genera il player widget di Apple Music."""
    q_enc = urllib.parse.quote(query)
    return {
        "title": f"Musica: {query}",
        "embed_url": f"https://embed.music.apple.com/it/search?term={q_enc}",
        "source": "applemusic"
    }
