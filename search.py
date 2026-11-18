from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)

def search_web(query: str, max_results: int = 4) -> list[dict]:
    """Esegue una ricerca web pulita e restituisce titolo, snippet e link."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, region="it-it", max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "snippet": r.get("body", ""),
                    "url": r.get("href", "")
                }
                for r in results
            ]
    except Exception as e:
        logger.error(f"Errore search_web: {e}")
        return []

def search_images(query: str, max_results: int = 4) -> list[dict]:
    """Recupera immagini reali da internet da mostrare nel Visual HUD."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.images(query, region="it-it", safesearch="moderate", max_results=max_results))
            return [
                {
                    "title": r.get("title", query),
                    "image_url": r.get("image", ""),
                    "thumbnail": r.get("thumbnail", r.get("image", "")),
                    "source_url": r.get("url", "")
                }
                for r in results
                if r.get("image")
            ]
    except Exception as e:
        logger.error(f"Errore search_images: {e}")
        return []
