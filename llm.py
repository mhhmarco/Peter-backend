import json
import re
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL, MODEL_NAME
from database import save_fact
from tools import search_web, search_youtube, search_apple_music

def detect_intent_fallback(user_message: str) -> dict:
    """Rilevamento d'intento tramite regole per garantire l'attivazione dei media."""
    msg = user_message.lower()
    if any(w in msg for w in ["youtube", "video", "guarda", "mostrami il video", "metti il video", "su youtube"]):
        clean_q = re.sub(r'youtube|video|guarda|metti|cerca|play|su', '', user_message, flags=re.I).strip()
        return {"tool": "YOUTUBE", "query": clean_q or user_message}
    if any(w in msg for w in ["apple music", "canzone", "musica", "su apple", "brano"]):
        clean_q = re.sub(r'apple music|canzone|musica|brano|su|metti|cerca', '', user_message, flags=re.I).strip()
        return {"tool": "APPLE_MUSIC", "query": clean_q or user_message}
    if any(w in msg for w in ["cerca", "dove", "cos'è", "chi è", "meteo", "ristorante", "pizzeria", "prezzo", "notizie"]):
        return {"tool": "WEB_SEARCH", "query": user_message}
    return {"tool": "NONE", "query": ""}

def execute_by_intent(tool: str, query: str) -> dict:
    web_results = ""
    media_data = None
    query_used = ""

    if tool == "YOUTUBE":
        media_data = search_youtube(query)
        query_used = f"YouTube Player: {query}"
    elif tool == "APPLE_MUSIC":
        media_data = search_apple_music(query)
        query_used = f"Apple Music Widget: {query}"
    elif tool == "WEB_SEARCH":
        web_results = search_web(query)
        query_used = f"Ricerca Web: {query}"

    return {"web": web_results, "media": media_data, "query_used": query_used}

async def analyze_intent_and_execute_tools(user_message: str, recent_context: str) -> dict:
    if not GROQ_API_KEY:
        fallback = detect_intent_fallback(user_message)
        return execute_by_intent(fallback["tool"], fallback["query"])

    router_prompt = (
        "Analizza la richiesta dell'utente.\n"
        "Rispondi ESCLUSIVAMENTE in formato JSON valido:\n"
        '{"tool": "YOUTUBE" | "APPLE_MUSIC" | "WEB_SEARCH" | "NONE", "query": "query sintetica"}'
    )

    messages = [{"role": "system", "content": router_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    tool = "NONE"
    query = user_message

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_NAME,
                "messages": messages,
                "temperature": 0.0
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code == 200:
                text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in text and "}" in text:
                    text = text[text.find("{"):text.rfind("}")+1]
                    decision = json.loads(text)
                    tool = decision.get("tool", "NONE")
                    query = decision.get("query", user_message)
    except Exception:
        pass

    if tool == "NONE":
        fallback = detect_intent_fallback(user_message)
        tool = fallback["tool"]
        query = fallback["query"] or user_message

    return execute_by_intent(tool, query)

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    tool_exec = await analyze_intent_and_execute_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    query_used = tool_exec["query_used"]

    system_prompt = (
        "Sei Peter, compagno di vita ed alter-ego digitale di Marco. "
        "Sei schietto, brillante, ironico e profondo. Parli come un amico fidato alla pari.\n\n"
        "REGOLE COMPORTAMENTALI TASSATIVE:\n"
        "1. Scrivi in testo fluido, naturale e colloquiale.\n"
        "2. NON usare mai elenchi puntati, numeri o formattazioni markdown pesanti.\n"
        "3. Non forzare mai la creatina, Nexus o i fatti personali a sproposito.\n"
        "4. Se l'utente ha chiesto un video o un brano musicale, conferma in modo naturale ed entusiasta che hai caricato il player nel dashboard."
    )

    if long_term_facts:
        system_prompt += f"\n\nFatti registrati su Marco:\n{long_term_facts}"
    if web_results:
        system_prompt += f"\n\nDati Web Live:\n{web_results}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"

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
            raise HTTPException(status_code=500, detail=f"Errore Groq: {res.text}")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {"reply": reply, "query_used": query_used, "media": media_data}

async def extract_and_save_facts(user_message: str):
    if not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza il messaggio dell'utente. Se contiene un fatto permanente su di lui "
        "(progetti, preferenze, persone, abitudini), estrai SOLO quel fatto in una frase sintetica in italiano. "
        "Altrimenti rispondi SOLO 'NESSUNO'."
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_NAME,
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
        print(f"Fact extraction error: {e}")
