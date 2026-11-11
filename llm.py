import json
import re
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import save_fact, get_personality_settings, get_contacts
from tools import search_web, search_youtube, search_apple_music
from scraper import fetch_web_page

MODEL_FAST = "openai/gpt-oss-20b"
MODEL_SMART = "openai/gpt-oss-120b"
MODEL_FACT = "qwen/qwen3.8-27b"

async def model_1_route_tools(user_message: str, recent_context: str) -> dict:
    """MODEL 1: Genera decisioni di tool e determina cosa mostrare sullo Schermo Reattivo HUD."""
    if not GROQ_API_KEY:
        return {"web": "", "media": None, "screen": None, "query_used": ""}

    urls = re.findall(r'https?://[^\s]+', user_message)
    web_content = ""
    query_used = ""
    if urls:
        target_url = urls[0]
        web_content = await fetch_web_page(target_url)
        query_used = f"Web Scraper: {target_url}"

    system_prompt = (
        "Sei il motore di routing di Peter OS. Analizza la richiesta dell'utente.\n"
        "1. Determina se serve attivare un tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, NONE).\n"
        "2. Determina cosa mostrare sullo SCHERMO REATTIVO HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, CALENDAR, NONE).\n\n"
        "Rispondi SOLO in formato JSON valido:\n"
        '{\n'
        '  "tool": "YOUTUBE" | "APPLE_MUSIC" | "WEB_SEARCH" | "NONE",\n'
        '  "query": "query sintetica",\n'
        '  "screen_type": "PERSON_CARD" | "MEDIA_PLAYER" | "SEARCH_PREVIEW" | "NONE",\n'
        '  "screen_target": "nome persona, film, artista o argomento da visualizzare"\n'
        '}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    media_data = None
    screen_display = None

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_FAST,
                "messages": messages,
                "temperature": 0.0
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})

            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    decision = json.loads(raw_text)
                    tool = decision.get("tool", "NONE")
                    query = decision.get("query", user_message)
                    screen_type = decision.get("screen_type", "NONE")
                    screen_target = decision.get("screen_target", "")

                    if tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube Player: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url")}
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url")}
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Ricerca Web: {query}"
                        screen_display = {"type": "SEARCH_PREVIEW", "query": query, "content": web_content[:300]}

                    if screen_type == "PERSON_CARD" and screen_target:
                        all_contacts = get_contacts()
                        matched = next((c for c in all_contacts if screen_target.lower() in c['name'].lower()), None)
                        if matched:
                            screen_display = {"type": "PERSON_CARD", "person": matched}
                        else:
                            screen_display = {"type": "PERSON_CARD", "person": {"name": screen_target, "category": "amicizia", "notes": "Menzionato in conversazione"}}
    except Exception as e:
        print(f"Errore Model 1 Router: {e}")

    return {"web": web_content, "media": media_data, "screen": screen_display, "query_used": query_used}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    """MODEL 2: Genera la risposta conversazionale profonda ed empatica conoscendo lo stato visivo dello schermo."""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    screen_display = tool_exec["screen"]
    query_used = tool_exec["query_used"]

    personality = get_personality_settings()

    system_prompt = (
        f"Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco.\n"
        f"TONO DI VOCE: {personality.get('tone')}\n"
        f"LIVELLO DI INIZIATIVA: {personality.get('initiative_level')}\n"
        f"ISTRUZIONI SPECIALI: {personality.get('custom_instructions')}\n\n"
        "REGOLE COMPORTAMENTALI:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale (stile iMessage/Telegram).\n"
        "2. NON usare mai elenchi puntati, numerati o grassetti markdown (**così**).\n"
    )

    if screen_display:
        system_prompt += f"\n\n[STATO SCHERMO REATTIVO HUD ATTUALE]: Peter, sullo schermo centrale della dashboard stai mostrando all'utente questo elemento: {json.dumps(screen_display, ensure_ascii=False)}. Fai riferimento a quello che Marco vede a schermo se utile."
    if long_term_facts:
        system_prompt += f"\n\nFatti registrati su Marco:\n{long_term_facts}"
    if web_results:
        system_prompt += f"\n\nDati Web / Contenuto Pagina:\n{web_results}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"

    payload = {
        "model": MODEL_SMART,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Errore Groq: {res.text}")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {"reply": reply, "query_used": query_used, "media": media_data, "screen": screen_display}

async def extract_and_save_facts(user_message: str):
    """MODEL 3: Estrazione asincrona delle memorie a lungo termine."""
    if not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza il messaggio dell'utente. Se contiene un fatto permanente su di lui "
        "(progetti, preferenze, persone, abitudini, competenze), estrai SOLO quel fatto in una frase sintetica in italiano. "
        "Altrimenti rispondi SOLO 'NESSUNO'."
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_FACT,
                "messages": [
                    {"role": "system", "content": extraction_prompt},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.1
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code == 200:
                extracted = res.json()["choices"][0]["message"]["content"].strip()
                if extracted and extracted.upper() != "NESSUNO":
                    save_fact(extracted)
    except Exception as e:
        print(f"Errore Model 3 Fact Extraction: {e}")
