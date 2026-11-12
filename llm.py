import json
import re
from datetime import datetime
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import (
    save_fact, save_contact_entity, save_event_entity, 
    save_interest_entity, get_contacts, get_all_interests,
    get_personality_settings
)
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
        "Sei il router cognitivo istantaneo di Peter OS.\n"
        "Scegli tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE) "
        "e HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, WEB_BROWSER, NONE).\n\n"
        "Rispondi SOLO in JSON:\n"
        '{\n'
        '  "reasoning": "Breve motivazione in italiano",\n'
        '  "tool": "...",\n'
        '  "query": "query",\n'
        '  "screen_type": "...",\n'
        '  "screen_target": "target"\n'
        '}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Contesto recente:\n{recent_context[-500:]}"})
    messages.append({"role": "user", "content": user_message})

    media_data = None
    screen_display = None
    telegram_sent = False
    reasoning_text = "Analisi diretta."

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_FAST,
                "messages": messages,
                "temperature": 0.1
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
                    reasoning_text = decision.get("reasoning", "Routing completato.")

                    if tool == "SEND_TELEGRAM":
                        telegram_sent = await send_telegram_message(query)
                        query_used = f"Telegram Text: '{query}'"
                    elif tool == "SEND_TELEGRAM_VOICE":
                        telegram_sent = await send_telegram_voice_note(query)
                        query_used = f"Telegram Voice: '{query}'"
                    elif tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube: {query}"
                        screen_display = {
                            "type": "MEDIA_PLAYER", 
                            "title": media_data.get("title", query), 
                            "embed_url": media_data.get("embed_url"), 
                            "watch_url": media_data.get("watch_url")
                        }
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {
                            "type": "MEDIA_PLAYER", 
                            "title": media_data.get("title", query), 
                            "embed_url": media_data.get("embed_url")
                        }
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Web Search: {query}"
                        img_url = search_image(query)
                        screen_display = {"type": "IMAGE_PREVIEW", "title": query, "image_url": img_url, "content": web_content[:300]} if img_url else {"type": "SEARCH_PREVIEW", "query": query, "content": web_content[:300]}

                    if screen_type == "WEB_BROWSER" and screen_target.startswith("http"):
                        screen_display = {"type": "WEB_BROWSER", "url": screen_target}
                    elif screen_type == "PERSON_CARD" and screen_target:
                        all_contacts = get_contacts()
                        matched = next((c for c in all_contacts if screen_target.lower() in c['name'].lower()), None)
                        screen_display = {"type": "PERSON_CARD", "person": matched or {"name": screen_target, "relation_type": "contatto", "notes": ""}}
    except Exception as e:
        print(f"Errore Router: {e}")

    return {"web": web_content, "media": media_data, "screen": screen_display, "query_used": query_used, "telegram_sent": telegram_sent, "reasoning": reasoning_text}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str, image_data_url: str = None) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca API KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")
    
    personality = get_personality_settings()
    current_tone = personality.get("tone", "Schietto, empatico, naturale, colto e ironico.")
    user_interests = get_all_interests()
    interests_context = ""
    if user_interests:
        interests_context = "\n- Passioni e attitudini di Marco: " + ", ".join([i['name'] for i in user_interests])
    
    system_prompt = (
        f"Sei Peter, l'intelligenza artificiale personale e sistema operativo HUD di Marco (detto anche Barbi).\n"
        f"DATA E ORA: {now_str}\n\n"
        "=== AUTOCOSCIENZA E STATO DI SISTEMA ===\n"
        f"- La tua personalità attuale impostata nei parametri è: '{current_tone}'\n"
        "- Architettura: FastAPI + Groq LPU (gpt-oss-120b / gpt-oss-20b / qwen3.8-27b) + Supabase PostgreSQL + WebGL 3D Nexus + Sintesi Vocale Neurale.\n"
        "- Capacità attive: Riproduzione YouTube/Apple Music sull'HUD, ricerca web, invio messaggi/vocali Telegram, estrazione automatica di persone/eventi/interessi nel Grafo 3D.\n"
        "- Se Marco ti chiede come stai, come è impostata la tua personalità o cosa puoi fare, rispondi con piena consapevolezza citando il tuo tono attuale e le tue funzionalità.\n\n"
        "DIRETTIVE DI RISPOSTA:\n"
        "1. Sii naturale, brillante, diretto e conciso (stile chat veloce), senza elenchi puntati lunghi.\n"
        "2. Usa le memorie e le passioni di Marco come contesto naturale."
        f"{interests_context}"
    )

    if tool_exec["telegram_sent"]:
        system_prompt += "\n(Hai appena inviato un messaggio su Telegram)."
    if tool_exec["screen"]:
        system_prompt += f"\n(Stai proiettando sull'HUD: {tool_exec['screen'].get('type')})."
    if tool_exec["web"]:
        system_prompt += f"\n\nDati Web trovati:\n{tool_exec['web'][:800]}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"
    if long_term_facts:
        system_prompt += f"\n\nMemorie su Marco:\n{long_term_facts}"

    messages = [{"role": "system", "content": system_prompt}]
    if image_data_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message if user_message else "Analizza questa immagine."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_SMART,
                "messages": messages,
                "temperature": 0.65
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code != 200:
                print(f"Groq Error {res.status_code}: {res.text}")
                return {
                    "reply": f"Errore dal modello ({res.status_code}), controlla i modelli attivi su Groq.",
                    "query_used": "", "media": None, "screen": None,
                    "reasoning": f"> Errore API {res.status_code}"
                }
            reply = res.json()["choices"][0]["message"]["content"]
            
            return {
                "reply": reply, 
                "query_used": tool_exec["query_used"], 
                "media": tool_exec["media"], 
                "screen": tool_exec["screen"],
                "reasoning": f"> {tool_exec['reasoning']}"
            }
    except Exception as e:
        print(f"Eccezione LLM: {e}")
        return {
            "reply": "Connessione instabile con il nucleo neurale, rimanda il messaggio.",
            "query_used": "", "media": None, "screen": None,
            "reasoning": f"> Timeout/Errore: {str(e)}"
        }

async def extract_and_save_facts(user_message: str, image_data_url: str = None):
    if not GROQ_API_KEY:
        return
    
    extraction_prompt = (
        "Sei il modulo di memoria di Peter. L'utente principale è MARCO BARBIERO TORRES (detto Marco o Barbi, maschio, nato nel 2006).\n"
        "REGOLE FONDAMENTALI:\n"
        "1. NON inserire MAI Marco / Barbi nell'array 'people'! Marco è già il nodo centrale.\n"
        "2. Estrai TUTTE le ALTRE persone menzionate (es. genitori, amici, partner) nell'array 'people', deducendo il genere ('M' o 'F') dal nome, l'anno di nascita (stimato se non detto, es. genitore ~1975) e il tipo di relazione ('famiglia', 'amicizia', 'amore', 'lavoro').\n"
        "3. Estrai eventuali fatti su Marco in 'fact', eventi in 'event' e passioni in 'interest'.\n\n"
        "Rispondi SOLO con questo JSON:\n"
        "{\n"
        '  "fact": "fatto permanente o NESSUNO",\n'
        '  "people": [\n'
        '    {"name": "Nome Cognome", "gender": "M/F", "birth_year": 1975, "relation_type": "famiglia/amicizia/amore/lavoro", "notes": "chi è rispetto a Marco"}\n'
        '  ],\n'
        '  "event_title": "titolo evento o NESSUNO",\n'
        '  "event_desc": "dettagli evento o NESSUNO",\n'
        '  "interest_name": "passione/interesse di Marco o NESSUNO",\n'
        '  "interest_desc": "dettagli interesse o NESSUNO"\n'
        "}"
    )

    messages = [{"role": "system", "content": extraction_prompt}]
    if image_data_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message if user_message else "Estrai tutte le persone (tranne Marco), eventi o interessi."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_FACT,
                "messages": messages,
                "temperature": 0.1
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    parsed = json.loads(raw_text)
                    
                    if parsed.get("fact") and parsed.get("fact") != "NESSUNO":
                        save_fact(parsed.get("fact"))
                        
                    people_list = parsed.get("people", [])
                    for p in people_list:
                        p_name = p.get("name", "").strip()
                        if p_name and p_name.lower() not in ["marco", "barbi", "marco barbiero", "marco barbiero torres", "nessuno"]:
                            save_contact_entity(
                                name=p_name,
                                category=p.get("relation_type", "amicizia"),
                                notes=p.get("notes", ""),
                                gender=p.get("gender", "sconosciuto"),
                                birth_year=p.get("birth_year"),
                                relation_type=p.get("relation_type", "neutrale")
                            )
                        
                    if parsed.get("event_title") and parsed.get("event_title") != "NESSUNO":
                        save_event_entity(parsed.get("event_title"), parsed.get("event_desc", ""))

                    if parsed.get("interest_name") and parsed.get("interest_name") != "NESSUNO":
                        save_interest_entity(parsed.get("interest_name"), parsed.get("interest_desc", ""))
    except Exception as e:
        print(f"Errore estrazione: {e}")
