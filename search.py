from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 5) -> str:
    """Ricerca avanzata su DuckDuckGo per informazioni in tempo reale."""
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
    
