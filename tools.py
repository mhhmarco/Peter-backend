import httpx
from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 4) -> str:
    """Esegue ricerche web in tempo reale per luoghi, dati ufficiali e notizie."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"Fonte: {r['title']}\nDetagli: {r['body']}\nURL: {r['href']}")
        if results:
            return "\n---\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web: {e}")
    return ""

def search_youtube(query: str) -> dict:
    """Cerca video o brani su YouTube e restituisce il link per l'embed in dashboard."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.videos(query, max_results=2))
            if results:
                v = results[0]
                # Estrazione ID Video per player embed
                url = v.get("content", "")
                video_id = ""
                if "v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in url:
                    video_id = url.split("youtu.be/")[1].split("?")[0]
                
                return {
                    "title": v.get("title", query),
                    "url": url,
                    "embed_url": f"https://www.youtube.com/embed/{video_id}?autoplay=1" if video_id else "",
                    "source": "youtube"
                }
    except Exception as e:
        print(f"Errore ricerca YouTube: {e}")
    return {}

def search_apple_music(query: str) -> dict:
    """Genera il link di ricerca e widget per Apple Music."""
    formatted_query = query.replace(" ", "+")
    search_url = f"https://music.apple.com/it/search?term={formatted_query}"
    return {
        "title": f"Cerca '{query}' su Apple Music",
        "url": search_url,
        "embed_url": f"https://embed.music.apple.com/it/search?term={formatted_query}",
        "source": "applemusic"
    }
