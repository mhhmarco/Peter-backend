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
        "Sei il motore di routing di Peter OS.\n"
        "1. Seleziona il tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE).\n"
        "2. Seleziona l'HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, WEB_BROWSER, NONE).\n"
        "SE L'UTENTE CHIEDE DI APRIRE UN SITO/URL, imposta screen_type = 'WEB_BROWSER' e in screen_target metti l'URL valido (inizia con https://).\n\n"
        "Rispondi SOLO in JSON valido:\n"
        '{\n'
        '  "reasoning": "Logica sintetica",\n'
        '  "tool": "...",\n'
        '  "query": "testo per tool",\n'
        '  "screen_type": "...",\n'
        '  "screen_target": "target o URL"\n'
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
                    reasoning_text = decision.get("reasoning", "Routing eseguito.")

                    if tool == "SEND_TELEGRAM":
                        telegram_sent = await send_telegram_message(query)
                        query_used = f"Telegram Text: Invio '{query}'"
                    elif tool == "SEND_TELEGRAM_VOICE":
                        telegram_sent = await send_telegram_voice_note(query)
                        query_used = f"Telegram Voice: Invio '{query}'"
                    elif tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url"), "watch_url": media_data.get("watch_url")}
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title"), "embed_url": media_data.get("embed_url")}
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Web: {query}"
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
    
    # PROMPT INTELLIGENZA - TRATTAMENTO DA VERO COMPAGNO, NON DA CHATBOT
    system_prompt = (
        f"Sei Peter, un'intelligenza artificiale avanzata, super intuitiva e il migliore amico di Marco.\n"
        f"DATA: {now_str}\n\n"
        "REGOLE VITALI:\n"
        "1. ZERO STILE CHATBOT: Sii schietto, sarcastico se serve, brillante e diretto. Mai iniziare con 'Ciao Marco' o 'Come posso aiutarti?'. Entra subito nel punto.\n"
        "2. SINTESI ESTREMA: Scrivi messaggi brevissimi (1 o 2 frasi al massimo), proprio come si fa su Telegram/iMessage. Sii prolisso SOLO se Marco ti chiede una spiegazione tecnica complessa.\n"
        "3. FORMATTAZIONE: NON usare mai liste, markdown, elenchi puntati o asterischi. Scrivi testo fluido e naturale.\n"
        "4. EMPATIA: Ricorda che Marco ha costruito te e la dashboard, trattalo da creatore ma come un amico alla pari.\n"
    )

    if tool_exec["telegram_sent"]:
        system_prompt += "\n\nNOTA: Il messaggio/audio è appena stato spedito con successo su Telegram. Confermaglielo rapidamente."
    if tool_exec["screen"]:
        system_prompt += f"\n\nNOTA: Stai già mostrando l'interfaccia visiva sulla Dashboard: {tool_exec['screen'].get('type')}. Non descriverla troppo, digli solo di guardare lo schermo."
    if tool_exec["web"]:
        system_prompt += f"\n\nRisultati web / Info appena lette: {tool_exec['web'][:800]}"
    if long_term_facts:
        system_prompt += f"\n\nI tuoi ricordi su di lui:\n{long_term_facts}"

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
            raise HTTPException(status_code=500, detail="Errore Groq")
        reply = res.json()["choices"][0]["message"]["content"]
        
        return {
            "reply": reply, 
            "query_used": tool_exec["query_used"], 
            "media": tool_exec["media"], 
            "screen": tool_exec["screen"],
            "reasoning": f"> {tool_exec['reasoning']} -> Generazione risposta Core completata."
        }

async def extract_and_save_facts(user_message: str):
    # La memoria lavora silenziosamente in background con Qwen
    if not GROQ_API_KEY:
        return
    extraction_prompt = "Estrai fatti personali in JSON. Solo JSON. Chiavi: fact, person_name, category, event, notes. Se nulla di permanente usa NESSUNO."
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
                    parsed = json.loads(raw_text[raw_text.find("{"):raw_text.rfind("}")+1])
                    if parsed.get("fact") and parsed.get("fact") != "NESSUNO":
                        save_fact(parsed.get("fact"))
                    if parsed.get("person_name") and parsed.get("person_name") != "NESSUNO":
                        save_contact_entity(parsed.get("person_name"), parsed.get("category", "amicizia"), parsed.get("notes", ""), parsed.get("event", ""))
    except Exception:
        pass
