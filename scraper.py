import httpx
from bs4 import BeautifulSoup

async def fetch_web_page(url: str) -> str:
    """Scarica e pulisce il testo da qualsiasi pagina web o URL fornito."""
    if not url.startswith("http"):
        url = "https://" + url
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            res = await client.get(url, headers=headers)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                # Rimuove script e stili inutili
                for script in soup(["script", "style", "nav", "footer"]):
                    script.extract()
                text = soup.get_text(separator=' ', strip=True)
                return text[:5000] # Limita la dimensione per il contesto LLM
    except Exception as e:
        print(f"Errore lettura pagina web {url}: {e}")
    return ""
