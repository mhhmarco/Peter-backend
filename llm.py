import json
import re
import asyncio
from datetime import datetime
import httpx
from fastapi import HTTPException
from config import GROQ_API_KEY, GROQ_URL
from database import (
    save_fact, save_contact_entity, save_event_entity, 
    save_interest_entity, get_contacts, get_all_interests,
    get_personality_settings, supabase
)
from tools import search_web, search_youtube, search_apple_music, search_image, send_telegram_message, send_telegram_voice_note
from scraper import fetch_web_page

# --- ORCHESTRAZIONE MODELLI SECONDO I LIMITI GROQ ---
MODEL_ROUTER = "allam-2-7b"         # Modello rapido per il routing (limite separato 6K TPM)
MODEL_CHAT = "openai/gpt-oss-120b"  # Modello ultra-smart per la conversazione (limite 8K TPM)
MODEL_VISION = "qwen/qwen3.8-27b"   # Modello per immagini e worker di riserva (limite 8K TPM)

# Pool di modelli per l'estrazione dati parallela. Dividere il carico evita il blocco 413/429
WORKER_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b"
]

# --- HELPER FUNZIONE PER LIMITARE I TOKEN NELLA CHAT NORMALE ---
def truncate_text(text: str, max_chars: int, from_end: bool = False) -> str:
    """Previene il sovraccarico di payload per la cronologia chat"""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:] if from_end else text[:max_chars]

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
        "Sei il router di Peter OS. Scegli tool (YOUTUBE, APPLE_MUSIC, WEB_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE) "
        "e HUD (PERSON_CARD, MEDIA_PLAYER, SEARCH_PREVIEW, IMAGE_PREVIEW, WEB_BROWSER, NONE).\n"
        "Rispondi SOLO in JSON:\n"
        '{"reasoning": "Motivo", "tool": "...", "query": "...", "screen_type": "...", "screen_target": "..."}'
    )

    messages = [{"role": "system", "content": system_prompt}]
    
    if recent_context:
        safe_context = truncate_text(recent_context, 500, from_end=True)
        messages.append({"role": "system", "content": f"Contesto:\n{safe_context}"})
        
    messages.append({"role": "user", "content": truncate_text(user_message, 800)})

    media_data = None
    screen_display = None
    telegram_sent = False
    reasoning_text = "Analisi diretta."

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": MODEL_ROUTER,
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
                    reasoning_text = decision.get("reasoning", "Routing ok.")

                    if tool == "SEND_TELEGRAM":
                        telegram_sent = await send_telegram_message(query)
                        query_used = f"Telegram Text: '{query}'"
                    elif tool == "SEND_TELEGRAM_VOICE":
                        telegram_sent = await send_telegram_voice_note(query)
                        query_used = f"Telegram Voice: '{query}'"
                    elif tool == "YOUTUBE":
                        media_data = search_youtube(query)
                        query_used = f"YouTube: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title", query), "embed_url": media_data.get("embed_url"), "watch_url": media_data.get("watch_url")}
                    elif tool == "APPLE_MUSIC":
                        media_data = search_apple_music(query)
                        query_used = f"Apple Music: {query}"
                        screen_display = {"type": "MEDIA_PLAYER", "title": media_data.get("title", query), "embed_url": media_data.get("embed_url")}
                    elif tool == "WEB_SEARCH" and not web_content:
                        web_content = search_web(query)
                        query_used = f"Web Search: {query}"
                        img_url = search_image(query)
                        safe_web = truncate_text(web_content, 400)
                        screen_display = {"type": "IMAGE_PREVIEW", "title": query, "image_url": img_url, "content": safe_web} if img_url else {"type": "SEARCH_PREVIEW", "query": query, "content": safe_web}

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

    # --- INTERCETTAZIONE TESTI ENORMI ---
    # Se il testo è gigantesco, Peter risponde subito all'utente (bypassando l'errore 413) 
    # mentre extract_and_save_facts() lavorerà in background sui modelli multipli.
    is_mega_prompt = len(user_message) > 2500
    chat_message = user_message
    
    if is_mega_prompt:
        chat_message = (
            f"[SISTEMA INTERNO: Marco ha inviato un mega-file di testo di {len(user_message)} caratteri. "
            "Devi SOLO rispondere che hai ricevuto l'archivio, che lo stai frammentando e che "
            "i tuoi processi in background stanno estraendo i dati per il Nexus 3D. "
            "Rispondi con una battuta intelligente in puro stile Peter e nient'altro.]"
        )

    tool_exec = await model_1_route_tools(chat_message, recent_context)
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")
    
    personality = get_personality_settings()
    current_tone = personality.get("tone", "Schietto, empatico, naturale, colto e ironico.")
    
    # Memorie sempre limitate per evitare la saturazione (413) nella chat continua
    safe_long_term = truncate_text(long_term_facts, 2000)
    safe_recent_context = truncate_text(recent_context, 1200, from_end=True)
    safe_web_content = truncate_text(tool_exec["web"], 800)
    
    system_prompt = (
        f"Sei Peter, l'IA personale di Marco.\n"
        f"DATA/ORA: {now_str}\n"
        f"- Tono: '{current_tone}'\n"
        "Sii conciso e brillante.\n"
    )

    if safe_web_content:
        system_prompt += f"\nWeb Data:\n{safe_web_content}"
    if safe_long_term:
        system_prompt += f"\nMemorie Base:\n{safe_long_term}"
    if safe_recent_context:
        system_prompt += f"\nChat Recente:\n{safe_recent_context}"

    model_to_use = MODEL_VISION if image_data_url else MODEL_CHAT
    messages = [{"role": "system", "content": system_prompt}]
    
    if image_data_url:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": chat_message if not is_mega_prompt else "Analizza questo input."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": chat_message})

    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": model_to_use,
                "messages": messages,
                "temperature": 0.5
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code != 200:
                return {
                    "reply": f"Sovraccarico Neurale ({res.status_code}). Riprova con un testo più corto.",
                    "query_used": "", "media": None, "screen": None, "reasoning": f"> API Error {res.status_code}"
                }
            
            return {
                "reply": res.json()["choices"][0]["message"]["content"], 
                "query_used": tool_exec["query_used"], 
                "media": tool_exec["media"], 
                "screen": tool_exec["screen"],
                "reasoning": f"> {tool_exec['reasoning']}"
            }
    except Exception as e:
        return {
            "reply": "Connessione neurale instabile. Forse il testo era ancora troppo grande.",
            "query_used": "", "media": None, "screen": None, "reasoning": f"> Errore: {str(e)}"
        }

# --- FUNZIONE WORKER PER IL CHUNKING PARALLELO ---
async def process_chunk(chunk: str, model: str, index: int, image_data_url: str = None):
    """Elabora un singolo pezzo di testo usando un modello specifico"""
    extraction_prompt = (
        "Sei l'estrattore dati di Peter. Utente: Marco Barbiero Torres.\n"
        "Estrai IN MODO SILENZIOSO in JSON le entità che trovi in questo blocco di testo:\n"
        '{"fact": "...", "people": [{"name": "...", "gender": "M/F", "birth_year": 1975, "relation_type": "...", "notes": "..."}], "event_title": "...", "event_desc": "...", "interest_name": "...", "interest_desc": "..."}'
    )
    
    messages = [{"role": "system", "content": extraction_prompt}]
    
    if image_data_url and index == 0:
        messages.append({
            "role": "user",
            "content": [
                {"type": "text", "text": chunk if chunk else "Estrai info."},
                {"type": "image_url", "image_url": {"url": image_data_url}}
            ]
        })
    else:
        messages.append({"role": "user", "content": f"Estrai JSON da qui:\n\n{chunk}"})

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(GROQ_URL, json={
                "model": model,
                "messages": messages,
                "temperature": 0.1
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})
            
            if res.status_code == 200:
                raw_text = res.json()["choices"][0]["message"]["content"].strip()
                if "{" in raw_text and "}" in raw_text:
                    raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                    parsed = json.loads(raw_text)
                    
                    if parsed.get("fact") and parsed.get("fact") != "NESSUNO":
                        fact_text = parsed.get("fact")
                        save_fact(fact_text)
                        if supabase:
                            try:
                                node_id = f"fact_{abs(hash(fact_text))}"
                                supabase.table("nodes").upsert({"id": node_id, "name": fact_text[:28], "type": "memory", "category": "memory", "notes": fact_text}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "memoria"}).execute()
                            except Exception: pass
                    
                    people_list = parsed.get("people", [])
                    for p in people_list:
                        p_name = p.get("name", "").strip()
                        if p_name and p_name.lower() not in ["marco", "barbi", "marco barbiero", "marco barbiero torres", "nessuno"]:
                            save_contact_entity(name=p_name, category=p.get("relation_type", "amicizia"), notes=p.get("notes", ""), gender=p.get("gender", "sconosciuto"), birth_year=p.get("birth_year"), relation_type=p.get("relation_type", "neutrale"))
                            if supabase:
                                try:
                                    node_id = f"contact_{abs(hash(p_name))}"
                                    supabase.table("nodes").upsert({"id": node_id, "name": p_name, "type": "person", "category": p.get("relation_type", "amicizia"), "notes": p.get("notes", ""), "gender": p.get("gender", "sconosciuto"), "birth_year": p.get("birth_year"), "relation_type": p.get("relation_type", "neutrale")}).execute()
                                    supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": p.get("relation_type", "neutrale")}).execute()
                                except Exception: pass
                    
                    if parsed.get("event_title") and parsed.get("event_title") != "NESSUNO":
                        ev_title = parsed.get("event_title")
                        save_event_entity(ev_title, parsed.get("event_desc", ""))
                        if supabase:
                            try:
                                node_id = f"event_{abs(hash(ev_title))}"
                                supabase.table("nodes").upsert({"id": node_id, "name": ev_title[:26], "type": "event", "category": "event", "notes": parsed.get("event_desc", "")}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "evento"}).execute()
                            except Exception: pass

                    if parsed.get("interest_name") and parsed.get("interest_name") != "NESSUNO":
                        int_name = parsed.get("interest_name")
                        save_interest_entity(int_name, parsed.get("interest_desc", ""))
                        if supabase:
                            try:
                                node_id = f"interest_{abs(hash(int_name))}"
                                supabase.table("nodes").upsert({"id": node_id, "name": int_name[:26], "type": "interest", "category": "interest", "notes": parsed.get("interest_desc", "")}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "passione"}).execute()
                            except Exception: pass
            else:
                print(f"Worker {model} fallito con status {res.status_code}")
    except Exception as e:
        print(f"Errore chunk worker {model}: {e}")

async def extract_and_save_facts(user_message: str, image_data_url: str = None):
    """
    SUDDIVISIONE E ORCHESTRAZIONE LLM MULTIPLI:
    Prende il testo, lo divide in chunk da ~2500 caratteri e assegna ogni chunk 
    a un modello LLM diverso dalla WORKER_MODELS pool in modo asincrono.
    """
    if not GROQ_API_KEY:
        return
    
    # Divisione in blocchi
    chunk_size = 2500
    chunks = [user_message[i:i+chunk_size] for i in range(0, len(user_message), chunk_size)]
    
    tasks = []
    for index, chunk in enumerate(chunks):
        # Assegna un modello dalla pool in modo circolare per non saturarne nessuno
        if image_data_url and index == 0:
            assigned_model = MODEL_VISION
        else:
            assigned_model = WORKER_MODELS[index % len(WORKER_MODELS)]
        
        # Crea il task asincrono
        task = asyncio.create_task(process_chunk(chunk, assigned_model, index, image_data_url))
        tasks.append(task)
        
        # Aggiunge un delay minimo tra un'assegnazione e l'altra se i chunk sono tantissimi
        if index > 0 and index % len(WORKER_MODELS) == 0:
            await asyncio.sleep(2)
            
    # Esegue tutti i chunk in background contemporaneamente sui diversi modelli!
    if tasks:
        await asyncio.gather(*tasks)
