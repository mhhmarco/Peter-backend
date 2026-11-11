import json
import re
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import save_fact
from tools import search_web, search_youtube, search_apple_music
from scraper import fetch_web_page

MODEL_FAST = "openai/gpt-oss-20b"        # Model 1: Router & Tool Dispatcher
MODEL_SMART = "openai/gpt-oss-120b"      # Model 2: Conversational Core Empatico
MODEL_FACT = "qwen/qwen3.8-27b"          # Model 3: Background Fact Extraction

async def model_1_route_tools(user_message: str, recent_context: str) -> dict:
    """MODEL 1 (Fast Router): Rileva l'intento, URL web o tool multimediali."""
    if not GROQ_API_KEY:
        return {"web": "", "media": None, "query_used": ""}

    # Controllo presenza URL nel messaggio
    urls = re.findall(r'https?://[^\s]+', user_message)
    web_content = ""
    query_used = ""
    if urls:
        target_url = urls[0]
        web_content = await fetch_web_page(target_url)
        query_used = f"Web Scraper: {target_url}"

    system_prompt = (
        "Sei il motore di routing di Peter OS. Analizza la richiesta dell'utente.\n"
        "Determina se serve attivare uno dei seguenti strumenti:\n"
        "- YOUTUBE: per video, brani musicali o trailer su YouTube.\n"
        "- APPLE_MUSIC: per brani o album su Apple Music.\n"
        "- WEB_SEARCH: per dati in tempo reale, locali, meteo, notizie o ricerche.\n"
        "- NONE: conversazione normale.\n\n"
        "Rispondi SOLO ed ESCLUSIVAMENTE in formato JSON valido:\n"
        '{"tool": "YOUTUBE" | "APPLE_MUSIC" | "WEB_SEARCH" | "NONE", "query": "query sintetica"}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    media_data = None

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

                    if tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube Player: {query}"
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Ricerca Web: {query}"
    except Exception as e:
        print(f"Errore Model 1 Router: {e}")

    return {"web": web_content, "media": media_data, "query_used": query_used}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    """MODEL 2 (Smart Core): Genera la risposta conversazionale profonda ed empatica."""
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    query_used = tool_exec["query_used"]

    system_prompt = (
        "Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco. "
        "Sei schietto, naturale, colto e ironico. Parli da amico fidato, alla pari.\n\n"
        "REGOLE COMPORTAMENTALI:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale (stile iMessage/Telegram).\n"
        "2. NON usare mai elenchi puntati, numerati o grassetti markdown (**così**).\n"
        "3. Se l'utente ti passa un link web o una pagina, analizzane i contenuti e commentali in modo naturale."
    )

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
        
        return {"reply": reply, "query_used": query_used, "media": media_data}

async def extract_and_save_facts(user_message: str):
    """MODEL 3 (Background Fact Processor): Estrazione asincrona delle memorie."""
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
