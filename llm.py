import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL, MODEL_NAME
from database import save_fact
from search import search_web

async def generate_search_query_if_needed(user_message: str, recent_context: str) -> str:
    """Utilizza l'LLM per determinare se serve cercare sul web e genera la query ottimale."""
    if not GROQ_API_KEY:
        return ""

    router_prompt = (
        "Analizza la richiesta dell'utente e il contesto recente della conversazione.\n"
        "Determina se la richiesta richiede dati aggiornati dal web, notizie, ricerche su software/emulatori/progetti, "
        "locali, luoghi, meteo o eventi reali.\n"
        "Se SERVE una ricerca web, rispondi ESATTAMENTE con la stringa della query di ricerca (es. 'Azahar Nintendo 3DS emulator').\n"
        "Se NON serve alcuna ricerca web, rispondi tassativamente SOLO con 'NO_SEARCH'."
    )

    messages = [
        {"role": "system", "content": router_prompt}
    ]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.0
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code == 200:
                query = res.json()["choices"][0]["message"]["content"].strip()
                if query and query.upper() != "NO_SEARCH":
                    return query
    except Exception as e:
        print(f"Errore routing ricerca: {e}")
    return ""

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    # 1. Routing autonomo della ricerca web
    search_query = await generate_search_query_if_needed(user_message, recent_context)
    web_results = ""
    if search_query:
        web_results = search_web(search_query)

    # 2. Construction System Prompt
    system_prompt = (
        "Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco. "
        "Sei schietto, naturale, colto e ironico. Parli da amico fidato, alla pari.\n\n"
        "REGOLE COMPORTAMENTALI FONDAMENTALI:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale, come su iMessage o Telegram.\n"
        "2. NON usare mai elenchi puntati, numeri, o grassetti markdown (**così**).\n"
        "3. Usa i fatti personali registrati SOLO se pertinenti al discorso. Non forzarli mai fuori contesto.\n"
        "4. Quando ricevi dati dalla ricerca web, basati RIGOROSAMENTE su di essi per fornire informazioni accurate e reali."
    )

    if long_term_facts:
        system_prompt += f"\n\nMemoria a lungo termine su Marco:\n{long_term_facts}"

    if web_results:
        system_prompt += f"\n\nRisultati RICERCA WEB LIVE per '{search_query}':\n{web_results}"

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
        reply = data["choices"][0]["message"]["content"]
        return {"reply": reply, "searched_query": search_query}

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
