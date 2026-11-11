import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL, MODEL_NAME
from database import save_fact
from search import search_web, should_search_web

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> str:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    web_results = ""
    if should_search_web(user_message):
        web_results = search_web(user_message)

    system_prompt = (
        "Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco. "
        "Sei schietto, naturale, colto e ironico. Parli da amico fidato, alla pari.\n\n"
        "REGOLE COMPORTAMENTALI FONDAMENTALI:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale, come su iMessage o Telegram.\n"
        "2. NON usare mai elenchi puntati, numeri, o grassetti markdown (**così**).\n"
        "3. USA I FATTI PERSONALI (es. creatina, progetti) SOLO SE STRETTAMENTE PERTINENTI. Non forzarli mai in risposte su cibo, indicazioni o ricerche generali.\n"
        "4. Se sono presenti risultati dalla ricerca web, usali per dare informazioni REALI ed ESATTE senza inventare posti o indirizzi."
    )

    if long_term_facts:
        system_prompt += f"\n\nMemoria a lungo termine su Marco:\n{long_term_facts}"

    if web_results:
        system_prompt += f"\n\nRisultati RICERCA WEB in tempo reale (USA QUESTI DATI REALI):\n{web_results}"

    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Errore Groq ({res.status_code}): {res.text}")
        data = res.json()
        return data["choices"][0]["message"]["content"]

async def extract_and_save_facts(user_message: str):
    if not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza il messaggio dell'utente. Se contiene un fatto rilevante o permanente su di lui "
        "(es. progetti, preferenze, persone importanti, idee, abitudini, competenze), "
        "estrai SOLO quel fatto in una frase sintetica in italiano. "
        "Se NON contiene alcun fatto personale rilevante, rispondi SOLO 'NESSUNO'."
    )

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code == 200:
                extracted = res.json()["choices"][0]["message"]["content"].strip()
                if extracted and extracted.upper() != "NESSUNO":
                    save_fact(extracted)
    except Exception as e:
        print(f"Errore fact extraction: {e}")
