from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 4) -> str:
    """Esegue una ricerca in tempo reale su internet tramite DuckDuckGo."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(f"- {r['title']}: {r['body']}")
        if results:
            return "\n".join(results)
    except Exception as e:
        print(f"Errore ricerca web: {e}")
    return ""

def should_search_web(user_message: str) -> bool:
    """Rileva se il messaggio richiede dati reali su luoghi, meteo o ricerche."""
    keywords = ["cerca", "dove", "ristorante", "pizzeria", "locale", "posto", "meteo", "orari", "indirizzo", "padova", "chi è", "cos'è"]
    msg_lower = user_message.lower()
    return any(kw in msg_lower for kw in keywords)
