import json
import re
from datetime import datetime
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import save_fact, save_contact_entity, save_event_entity, get_contacts
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
        "Sei il motore di routing di Peter OS.\n"
        "Scegli il tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE) "
        "e l'HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, WEB_BROWSER, NONE).\n\n"
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

async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca API KEY")

    tool_exec = await model_1_route_tools(user_message, recent_context)
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")
    
    system_prompt = (
        f"Sei Peter, intelligenza artificiale avanzata e migliore amico di Marco.\n"
        f"DATA ATTUALE: {now_str}\n\n"
        "DIRETTIVE:\n"
        "1. Sfrutta il contesto per collegare i discorsi precedenti.\n"
        "2. Rispondi in modo brevissimo, diretto e colloquiale (stile iMessage), senza elenchi puntati o markdown pesante.\n"
    )

    if tool_exec["telegram_sent"]:
        system_prompt += "\n\n(Azione Telegram eseguita)."
    if tool_exec["screen"]:
        system_prompt += f"\n\n(HUD attivo: {tool_exec['screen'].get('type')})."
    if tool_exec["web"]:
        system_prompt += f"\n\nRisultati web:\n{tool_exec['web'][:800]}"
    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"
    if long_term_facts:
        system_prompt+= f"\n\nMemorie permanenti:\n{long_term_facts}"

    payload = {
        "model": MODEL_SMART,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
    }

    async with httpx.AsyncClient(timeout=25.0) as client:
        res = await client.post(GROQ_URL, json=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
        if res.status_code != 200:
            raise HTTPException(status_code=500, detail="Errore Groq Core")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {
            "reply": reply, 
            "query_used": tool_exec["query_used"], 
            "media": tool_exec["media"], 
            "screen": tool_exec["screen"],
            "reasoning": f"> Analisi contesto: {tool_exec['reasoning']}"
        }

async def extract_and_save_facts(user_message: str):
    if not GROQ_API_KEY:
        return
    extraction_prompt = (
        "Analizza il messaggio ed estrai entità in JSON rigoroso:\n"
        "{\n"
        '  "fact": "fatto o memoria permanente su Marco o NESSUNO",\n'
        '  "person_name": "nome della persona menzionata (es. Beatrice, Salmez, Takuro) o NESSUNO",\n'
        '  "category": "famiglia" o "amicizia" o "fidanzata" o "lavoro",\n'
        '  "birthday": "data di compleanno o nascita se menzionata (es. 20 dicembre 2004) o NESSUNO",\n'
        '  "notes": "dettagli o relazioni associate alla persona o NESSUNO",\n'
        '  "event_title": "titolo evento o appuntamento o NESSUNO",\n'
        '  "event_desc": "dettagli evento o NESSUNO"\n'
        "}"
    )
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_FACT,
                "messages": [{"role": "system", "content": extraction_prompt}, {"role": "user", "content": user_message}],
                "temperature": 0.1
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    parsed = json.loads(raw_text)
                    
                    fact = parsed.get("fact")
                    if fact and fact.upper() != "NESSUNO":
                        save_fact(fact)
                        
                    person = parsed.get("person_name")
                    if person and person.upper() != "NESSUNO":
                        save_contact_entity(
                            name=person,
                            category=parsed.get("category", "amicizia"),
                            notes=parsed.get("notes", ""),
                            birthday=parsed.get("birthday", "")
                        )
                        
                    ev_title = parsed.get("event_title")
                    if ev_title and ev_title.upper() != "NESSUNO":
                        save_event_entity(ev_title, parsed.get("event_desc", ""))
    except Exception as e:
        print(f"Errore estrazione entità: {e}")
