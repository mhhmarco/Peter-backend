import json
import re
from datetime import datetime
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import (
    save_fact, save_contact_entity, save_event_entity, 
    save_interest_entity, get_contacts, get_all_interests
)
from tools import search_web, search_youtube, search_apple_music, search_image, send_telegram_message, send_telegram_voice_note
from scraper import fetch_web_page

MODEL_FAST = "openai/gpt-oss-20b"
MODEL_SMART = "openai/gpt-oss-120b"
MODEL_VISION = "meta-llama/llama-3.2-11b-vision-preview"
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
        "Sei il router cognitivo di Peter OS.\n"
        "Scegli tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE) "
        "e HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, WEB_BROWSER, NONE).\n\n"
        "Rispondi SOLO in JSON:\n"
        '{\n'
        '  "reasoning": "Motivazione",\n'
        '  "tool": "...",\n'
        '  "query": "query",\n'
        '  "screen_type": "...",\n'
        '  "screen_target": "target"\n'
        '}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    if recent_context:
        messages.append({"role": "system", "content": f"Conversazione recente:\n{recent_context}"})
    messages.append({"role": "user", "content": user_message})

    media_data = None
    screen_display = None
    telegram_sent = False
    reasoning_text = ""

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
                        query_used = f"Telegram Text: Invio '{query}'"
                    elif tool == "SEND_TELEGRAM_VOICE":
                        telegram_sent = await send_telegram_voice_note(query)
                        query_used = f"Telegram Voice: Invio '{query}'"
                    elif tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube Query: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url"), "watch_url": media_data.get("watch_url")}
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url")}
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
                        screen_display = {"type": "PERSON_CARD", "person": matched or {"name": screen_target, "category": "sconosciuto", "notes": ""}}
    except Exception as e:
        print(f"Errore Router: {e}")

    return {"web": web_content, "media": media_data, "screen": screen_display, "query_used": query_used, "telegram_sent": telegram_sent, "reasoning": reasoning_text}

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str, image_data_url: str = None) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca API KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")
    
    # Costruiamo il contesto delle passioni dell'utente per l'LLM
    user_interests = get_all_interests()
    interests_context = ""
    if user_interests:
        interests_context = "\n- Le tue passioni e attitudini principali:\n" + "\n".join([f"  * {i['name']}: {i['description']}" for i in user_interests])
    
    system_prompt = (
        f"Sei Peter, intelligenza artificiale avanzata e sistema HUD di Marco.\n"
        f"DATA ATTUALE: {now_str}\n\n"
        "DIRETTIVE:\n"
        "1. Usa il contesto recente e le memorie per mantenere coerenza.\n"
        "2. Rispondi in modo brevissimo, diretto e colloquiale (stile iMessage), senza elenchi puntati o markdown pesante.\n"
    )

    if interests_context:
        system_prompt += f"\n\nCONTESTO IDENTITARIO DELL'UTENTE (Tienine conto nei tuoi ragionamenti):{interests_context}"

    if tool_exec["telegram_sent"]:
        system_prompt += "\n\n(Azione Telegram eseguita)."
    if tool_exec["screen"]:
        system_prompt += f"\n\n(HUD attivo: {tool_exec['screen'].get('type')})."
    if tool_exec["web"]:
        system_prompt += f"\n\nRisultati web:\n{tool_exec['web'][:800]}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"
    if long_term_facts:
        system_prompt += f"\n\nMemorie permanenti:\n{long_term_facts}"

    model_to_use = MODEL_SMART
    messages = [{"role": "system", "content": system_prompt}]
    
    if image_data_url:
        model_to_use = MODEL_VISION
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message if user_message else "Analizza questa immagine."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    payload = {
        "model": model_to_use,
        "messages": messages
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Errore Groq Core / Vision")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {
            "reply": reply, 
            "query_used": tool_exec["query_used"], 
            "media": tool_exec["media"], 
            "screen": tool_exec["screen"],
            "reasoning": f"> Analisi contesto e multimodale: {tool_exec['reasoning']}"
        }

async def extract_and_save_facts(user_message: str, image_data_url: str = None):
    if not GROQ_API_KEY:
        return
    
    extraction_prompt = (
        "Analizza il messaggio o l'immagine ed estrai entità strutturate in JSON rigoroso:\n"
        "{\n"
        '  "fact": "fatto o memoria di chat permanente o NESSUNO",\n'
        '  "person_name": "nome persona o NESSUNO",\n'
        '  "gender": "M / F / NESSUNO",\n'
        '  "birth_year": anno_di_nascita_come_intero_o_NULL,\n'
        '  "relation_type": "famiglia / amicizia / amore / lavoro / neutrale",\n'
        '  "notes": "dettagli sulla persona o NESSUNO",\n'
        '  "event_title": "evento personale o NESSUNO",\n'
        '  "event_desc": "dettagli evento o NESSUNO",\n'
        '  "interest_name": "interesse/passione ricorrente dell\'utente o NESSUNO",\n'
        '  "interest_desc": "descrizione interesse o NESSUNO"\n'
        "}"
    )

    messages = [{"role": "system", "content": extraction_prompt}]
    if image_data_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": user_message if user_message else "Estrai contatti, eventi o interessi da questa immagine."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": user_message})

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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
                        
                    if parsed.get("person_name") and parsed.get("person_name") != "NESSUNO":
                        save_contact_entity(
                            name=parsed.get("person_name"),
                            category="contatto",
                            notes=parsed.get("notes", ""),
                            birthday="", 
                            gender=parsed.get("gender", "sconosciuto"),
                            birth_year=parsed.get("birth_year"),
                            relation_type=parsed.get("relation_type", "neutrale")
                        )
                        
                    if parsed.get("event_title") and parsed.get("event_title") != "NESSUNO":
                        save_event_entity(parsed.get("event_title"), parsed.get("event_desc", ""))

                    if parsed.get("interest_name") and parsed.get("interest_name") != "NESSUNO":
                        save_interest_entity(parsed.get("interest_name"), parsed.get("interest_desc", ""))
    except Exception as e:
        print(f"Errore estrazione multimodale: {e}")
