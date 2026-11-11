import json
import re
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import (
    save_fact_deduplicated, 
    add_or_update_node, 
    get_graph_data
)
from tools import search_web, search_youtube, search_apple_music

MODEL_FAST = "openai/gpt-oss-20b"        # Model 1: Router & Tool Dispatcher
MODEL_SMART = "openai/gpt-oss-120b"      # Model 2: Conversational Core Empatico
MODEL_FACT = "qwen/qwen3.8-27b"          # Model 3: Background Entity & Clarification Processor

def clean_json_response(raw_text: str) -> dict:
    try:
        match = re.search(r'\{.*\}', raw_text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except Exception as e:
        print(f"Errore parsing JSON: {e}")
    return {}

async def model_1_route_tools(user_message: str, recent_context: str) -> dict:
    if not GROQ_API_KEY:
        return {"web": "", "media": None, "query_used": ""}

    system_prompt = (
        "Sei il motore di routing di Peter OS. Analizza la richiesta dell'utente.\n"
        "Determina se serve attivare uno dei seguenti strumenti:\n"
        "- YOUTUBE: per video, brani musicali o trailer su YouTube.\n"
        "- APPLE_MUSIC: per brani o album su Apple Music.\n"
        "- WEB_SEARCH: per dati in tempo reale, notizie, informazioni aggiornate.\n"
        "- NONE: conversazione normale.\n\n"
        "Rispondi SCRIVENDO SOLO ED ESCLUSIVAMENTE IL SEGUENTE JSON VALIDO:\n"
        '{"tool": "YOUTUBE" | "APPLE_MUSIC" | "WEB_SEARCH" | "NONE", "query": "query sintetica"}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    web_results, media_data, query_used = "", None, ""

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(
                GROQ_URL,
                json={"model": MODEL_FAST, "messages": messages, "temperature": 0.0},
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
            )

            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                decision = clean_json_response(raw_text)
                tool = decision.get("tool", "NONE")
                query = decision.get("query", user_message)

                if tool == "YOUTUBE":
                    media_data = search_youtube(query)
                    query_used = f"YouTube: {query}"
                elif tool == "APPLE_MUSIC":
                    media_data = search_apple_music(query)
                    query_used = f"Apple Music: {query}"
                elif tool == "WEB_SEARCH":
                    web_results = search_web(query)
                    query_used = f"Ricerca Web: {query}"
    except Exception as e:
        print(f"Errore Model 1 Router ({MODEL_FAST}): {e}")

    return {"web": web_results, "media": media_data, "query_used": query_used}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str, pending_clarification: str = "") -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    query_used = tool_exec["query_used"]

    system_prompt = (
        "Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco.\n"
        "Sei schietto, naturale, colto e ironico. Parli da amico fidato, alla pari.\n\n"
        "REGOLE COMPORTAMENTALI:\n"
        "1. Scrivi in testo fluido e naturale (stile iMessage/Telegram).\n"
        "2. Evita elenchi puntati forzati o formattazioni pesanti.\n"
        "3. Se ti viene segnalata una NUOVA PERSONA senza relazione chiara, CHIEDI NATURALMENTE A MARCO CHI È E CHE RUOLO HA."
    )

    if pending_clarification:
        system_prompt += f"\n\nNOTA SISTEMA: Marco ha appena menzionato '{pending_clarification}', ma non sai chi sia. Chiedigli con naturalezza chi è e che relazione hanno per aggiungerlo alla mappa Nexus."

    if long_term_facts:
        system_prompt += f"\n\nFatti registrati su Marco:\n{long_term_facts}"
    if web_results:
        system_prompt += f"\n\nDati Web Live:\n{web_results}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"

    payload = {
        "model": MODEL_SMART,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Errore Groq: {res.text}")
        reply = res.json()["choices"][0]["message"]["content"]

        return {"reply": reply, "query_used": query_used, "media": media_data}

async def process_background_memory(user_message: str):
    """MODEL 3: Rileva entità non note e salva automaticamente i nuovi contatti nel Nexus."""
    if not GROQ_API_KEY:
        return

    graph = get_graph_data()
    existing_names = [n["name"].lower() for n in graph.get("nodes", [])]

    extraction_prompt = (
        "Analizza il messaggio dell'utente ed estrai:\n"
        "1. 'fact': fatto permanente su Marco o null.\n"
        "2. 'entity': nome proprio di persona menzionata o null.\n"
        "3. 'relationship': tipo di relazione o ruolo menzionato (es. 'amico', 'collega', 'fratello', 'sconosciuto').\n"
        "4. 'category': 'Amicizia', 'Famiglia', 'Lavoro', 'Progetto'.\n\n"
        "Rispondi SOLO in JSON formato:\n"
        '{"fact": "stringa o null", "entity": "stringa o null", "relationship": "stringa", "category": "stringa"}'
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                GROQ_URL,
                json={
                    "model": MODEL_FACT,
                    "messages": [
                        {"role": "system", "content": extraction_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "temperature": 0.1
                },
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"}
            )

            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                data = clean_json_response(raw_text)

                fact = data.get("fact")
                entity = data.get("entity")
                relationship = data.get("relationship", "")
                category = data.get("category", "Amicizia")

                if fact and len(fact) > 5 and str(fact).lower() != "null":
                    save_fact_deduplicated(fact)

                if entity and len(entity) > 2 and str(entity).lower() != "null":
                    # Salva l'entità nel Nexus se non già presente
                    add_or_update_node(entity, category=category, notes=f"Relazione: {relationship}")

    except Exception as e:
        print(f"Errore Background Processing ({MODEL_FACT}): {e}")
