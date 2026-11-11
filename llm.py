import json
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL, MODEL_NAME
from database import save_fact
from tools import search_web, search_youtube, search_apple_music

async def analyze_intent_and_execute_tools(user_message: str, recent_context: str) -> dict:
    """Utilizza un passaggio rapido con l'LLM per decidere quali strumenti attivare."""
    if not GROQ_API_KEY:
        return {"web": "", "media": None, "query_used": ""}

    router_prompt = (
        "Analizza il messaggio dell'utente. Determina se serve attivare uno dei seguenti tool:\n"
        "1. WEB_SEARCH: per dati reali, meteo, posti, emulatori specifici, notizie o fatti recenti.\n"
        "2. YOUTUBE: se chiede di cercare o riprodurre video, trailer o musica su YouTube.\n"
        "3. APPLE_MUSIC: se chiede esplicitamente brani, album o playlist su Apple Music.\n"
        "4. NONE: per conversazione standard, opinioni o risposte diretta.\n\n"
        "Rispondi ESATTAMENTE ed ESCLUSIVAMENTE in formato JSON valido come questo:\n"
        '{"tool": "WEB_SEARCH" | "YOUTUBE" | "APPLE_MUSIC" | "NONE", "query": "query di ricerca ottimizzata"}'
    )

    messages = [{"role": "system", "content": router_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto conversazione recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.0
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}

    web_results = ""
    media_data = None
    query_used = ""

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code == 200:
                text = res.json()["choices"][0]["message"]["content"].strip()
                # Pulizia formato json
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                
                decision = json.loads(text)
                tool = decision.get("tool", "NONE")
                query = decision.get("query", user_message)

                if tool == "WEB_SEARCH":
                    web_results = search_web(query)
                    query_used = f"Ricerca Web: {query}"
                elif tool == "YOUTUBE":
                    media_data = search_youtube(query)
                    query_used = f"YouTube Video: {query}"
                elif tool == "APPLE_MUSIC":
                    media_data = search_apple_music(query)
                    query_used = f"Apple Music: {query}"
    except Exception as e:
        print(f"Errore tool routing: {e}")

    return {"web": web_results, "media": media_data, "query_used": query_used}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    # 1. Esecuzione autonoma dei Tool (Web Search / YouTube / Apple Music)
    tool_exec = await analyze_intent_and_execute_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    query_used = tool_exec["query_used"]

    # 2. System Prompt per la vera personalità di Peter
    system_prompt = (
        "Sei Peter, un compagno di vita digitale ed alter-ego empatico di Marco. "
        "Sei schietto, naturale, colto, ironico e profondo. Parli come un amico fidato alla pari.\n\n"
        "REGOLE COMPORTAMENTALI TASSATIVE:\n"
        "1. Scrivi SOLO in testo fluido, caldo e colloquiale, come su iMessage o Telegram.\n"
        "2. NON usare mai elenchi puntati, numerati, o formattazione markdown pesante (niente grassetti **così**).\n"
        "3. Usa i fatti registrati in memoria SOLO quando sono strettamente collegati al discorso. NON citare mai creatina, Nexus o progetti a sproposito.\n"
        "4. Se sono presenti risultati web o media, usa quelle informazioni esatte per rispondere in modo preciso ed intelligente."
    )

    if long_term_facts:
        system_prompt += f"\n\nMemoria a lungo termine su Marco:\n{long_term_facts}"

    if web_results:
        system_prompt += f"\n\nDati REALI recuperati dal web:\n{web_results}"

    if recent_context:
        system_prompt += f"\n\nEstratto conversazione recente:\n{recent_context}"

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Errore Groq ({res.status_code}): {res.text}")
        data = res.json()
        reply = data["choices"][0]["message"]["content"]
        
        return {
            "reply": reply, 
            "query_used": query_used,
            "media": media_data
        }

async def extract_and_save_facts(user_message: str):
    if not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza il messaggio dell'utente. Se contiene un fatto rilevante o permanente su di lui "
        "(es. progetti, preferenze, persone importanti, abitudini, competenze, relazioni), "
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

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code == 200:
                extracted = res.json()["choices"][0]["message"]["content"].strip()
                if extracted and extracted.upper() != "NESSUNO":
                    save_fact(extracted)
    except Exception as e:
        print(f"Errore fact extraction: {e}")
