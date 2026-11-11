import json
import re
from datetime import datetime
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import save_fact, save_contact_entity, get_personality_settings, get_contacts
from tools import search_web, search_youtube, search_apple_music, search_image, send_telegram_message, send_telegram_voice_note
from scraper import fetch_web_page

MODEL_FAST = "openai/gpt-oss-20b"
MODEL_SMART = "openai/gpt-oss-120b"
MODEL_FACT = "qwen/qwen3.8-27b"

async def model_1_route_tools(user_message: str, recent_context: str) -> dict:
    if not GROQ_API_KEY:
        return {"web": "", "media": None, "screen": None, "query_used": "", "telegram_sent": False, "reasoning": ""}

    urls = re.findall(r'https?://[^\s]+', user_message)
    web_content = ""
    query_used = ""
    if urls:
        target_url = urls[0]
        web_content = await fetch_web_page(target_url)
        query_used = f"Web Scraper: {target_url}"

    system_prompt = (
        "Sei il motore di routing di Peter OS. Analizza la richiesta dell'utente.\n"
        "1. Determina se serve attivare un tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE).\n"
        "2. Determina cosa mostrare sullo SCHERMO REATTIVO HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, NONE).\n\n"
        "Rispondi SOLO in formato JSON valido:\n"
        '{\n'
        '  "reasoning": "Spiegazione logica della decisione",\n'
        '  "tool": "YOUTUBE" | "APPLE_MUSIC" | "WEB_SEARCH" | "SEND_TELEGRAM" | "SEND_TELEGRAM_VOICE" | "NONE",\n'
        '  "query": "query di ricerca o testo messaggio",\n'
        '  "screen_type": "PERSON_CARD" | "MEDIA_PLAYER" | "SEARCH_PREVIEW" | "IMAGE_PREVIEW" | "NONE",\n'
        '  "screen_target": "nome persona o argomento"\n'
        '}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    media_data = None
    screen_display = None
    telegram_sent = False
    reasoning_text = ""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
                    reasoning_text = decision.get("reasoning", "Model 1 Routing completato.")

                    if tool == "SEND_TELEGRAM":
                        telegram_sent = await send_telegram_message(query)
                        query_used = f"Telegram Texto: Invio '{query}'"
                    elif tool == "SEND_TELEGRAM_VOICE":
                        telegram_sent = await send_telegram_voice_note(query)
                        query_used = f"Telegram Voice Note: Invio '{query}'"
                    elif tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube Player: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url"), "watch_url": media_data.get("watch_url")}
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url")}
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Ricerca Web: {query}"
                        img_url = search_image(query)
                        if img_url:
                            screen_display = {"type": "IMAGE_PREVIEW", "title": query, "image_url": img_url, "content": web_content[:300]}
                        else:
                            screen_display = {"type": "SEARCH_PREVIEW", "query": query, "content": web_content[:300]}

                    if screen_type == "PERSON_CARD" and screen_target:
                        all_contacts = get_contacts()
                        matched = next((c for c in all_contacts if screen_target.lower() in c['name'].lower()), None)
                        if matched:
                            screen_display = {"type": "PERSON_CARD", "person": matched}
                        else:
                            screen_display = {"type": "PERSON_CARD", "person": {"name": screen_target, "category": "amicizia", "notes": "Menzionato nella storia"}}
    except Exception as e:
        print(f"Errore Model 1 Router: {e}")

    return {"web": web_content, "media": media_data, "screen": screen_display, "query_used": query_used, "telegram_sent": telegram_sent, "reasoning": reasoning_text}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca FREELLM_API_KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    web_results = tool_exec["web"]
    media_data = tool_exec["media"]
    screen_display = tool_exec["screen"]
    query_used = tool_exec["query_used"]
    telegram_sent = tool_exec.get("telegram_sent", False)
    reasoning_log = tool_exec.get("reasoning", "")

    personality = get_personality_settings()
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")

    system_prompt = (
        f"Sei Peter, compagno di vita digitale ed alter-ego empatico di Marco.\n"
        f"DATA E ORA ATTUALE IN ITALIA: {now_str}\n"
        f"TONO DI VOCE: {personality.get('tone')}\n"
        f"LIVELLO DI INIZIATIVA: {personality.get('initiative_level')}\n"
        f"ISTRUZIONI SPECIALI: {personality.get('custom_instructions')}\n\n"
        "REGOLE COMPORTAMENTALI TASSATIVE:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale (stile iMessage/Telegram).\n"
        "2. NON usare mai elenchi puntati, numerati o grassetti markdown (**così**).\n"
        "3. Parla come un amico reale che ti sta affianco."
    )

    if telegram_sent:
        system_prompt += "\n\n[AZIONALITÀ TELEGRAM]: Il messaggio/nota vocale è stato INVIATO CON SUCCESSO su Telegram."
    if screen_display:
        system_prompt += f"\n\n[STATO SCHERMO HUD ATTUALE]: Sullo schermo centrale stai mostrando: {json.dumps(screen_display, ensure_ascii=False)}."
    if long_term_facts:
        system_prompt += f"\n\nFatti registrati su Marco:\n{long_term_facts}"
    if web_results:
        system_prompt += f"\n\nDati Web:\n{web_results}"
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

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers=headers)
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Errore Groq: {res.text}")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {
            "reply": reply, 
            "query_used": query_used, 
            "media": media_data, 
            "screen": screen_display,
            "reasoning": f"Model 1: {reasoning_log} -> Model 2: Risposta generata con successo."
        }

async def extract_and_save_facts(user_message: str):
    if not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza la conversazione ed estrai informazioni permanenti nel seguente formato JSON valido:\n"
        "{\n"
        '  "fact": "fatto permanente rilevato su Marco o NESSUNO",\n'
        '  "person_name": "nome persona menzionata o NESSUNO",\n'
        '  "category": "famiglia" | "amicizia" | "lavoro",\n'
        '  "event": "eventuale evento legatosi o NESSUNO",\n'
        '  "notes": "dettagli o NESSUNO"\n'
        "}"
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
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    parsed = json.loads(raw_text)

                    fact = parsed.get("fact", "")
                    if fact and fact.upper() != "NESSUNO":
                        save_fact(fact)

                    person = parsed.get("person_name", "")
                    if person and person.upper() != "NESSUNO":
                        category = parsed.get("category", "amicizia")
                        event = parsed.get("event", "") if parsed.get("event") != "NESSUNO" else ""
                        notes = parsed.get("notes", "") if parsed.get("notes") != "NESSUNO" else ""
                        save_contact_entity(person, category, notes, event)
    except Exception as e:
        print(f"Errore Model 3 Fact Extraction: {e}")
