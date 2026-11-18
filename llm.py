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
    get_personality_settings, make_stable_id, supabase
)
from tools import (
    search_web, search_youtube, search_apple_music,
    search_image_result, send_telegram_message, send_telegram_voice_note
)
from scraper import fetch_web_page

MODEL_ROUTER = "llama-3.1-8b-instant"
MODEL_CHAT = "openai/gpt-oss-120b"
MODEL_VISION = "qwen/qwen3.8-27b"

WORKER_MODELS = [
    "openai/gpt-oss-20b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b"
]


def truncate_text(text: str, max_chars: int, from_end: bool = False) -> str:
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    return text[-max_chars:] if from_end else text[:max_chars]


def clean_reply_text(text: str) -> str:
    """Rimuove simboli Markdown sporchi (**, ###, tabelle |, link [a](b))."""
    if not text:
        return ""
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'(?<!\w)\*(?!\s)(.*?)(?<!\s)\*(?!\w)', r'\1', text)
    text = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    text = re.sub(r'`{1,3}', '', text)

    cleaned_lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")
            continue
        if set(stripped).issubset({'|', '-', ':', ' '}):
            continue
        if stripped.startswith('|') and stripped.endswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|') if c.strip()]
            cleaned_lines.append(" - ".join(cells))
        else:
            cleaned_lines.append(line)

    return re.sub(r'\n{3,}', '\n\n', "\n".join(cleaned_lines)).strip()


def _detect_intent_by_rules(user_message: str) -> tuple[str, str, str] | None:
    """
    Classificatore deterministico ad alta priorità:
    1. YouTube / Video / Canzoni (prima di 'mostrami'!)
    2. Apple Music
    3. Domande informative / biografiche / prezzi ('chi è', 'cos'è', 'quanto costa')
    4. Richieste visive pure ('mostrami', 'foto di', 'immagine di')
    """
    msg = user_message.strip()
    low = msg.lower()

    # 1. Media / Video / YouTube / Canzoni
    if any(k in low for k in ["youtube", "canzone", "brano", "video", "trailer", "videoclip", "ascolta", "riproduci", "metti musica"]):
        clean_q = re.sub(r'^(mostrami|fammi vedere|cerca|riproduci|metti|ascolta)\s+(una|un|il|la|lo)?\s*(canzone|brano|video|videoclip)?\s*(di|su)?\s*', '', low).strip()
        clean_q = re.sub(r'\s+(da youtube|su youtube)$', '', clean_q).strip() or msg
        if "apple music" in low:
            return ("APPLE_MUSIC", "MEDIA_PLAYER", clean_q)
        return ("YOUTUBE", "MEDIA_PLAYER", clean_q)

    # 2. Domande biografiche, fattuali, prezzi, notizie
    if any(k in low for k in ["chi è", "chi era", "chi sono", "cos'è", "cosa è", "cosa sono", "parlami di", "quanto costa", "prezzo di", "notizie su", "dove si trova"]):
        clean_q = re.sub(r'^(chi è|chi era|chi sono|cos\'è|cosa è|cosa sono|parlami di|quanto costa|prezzo di|notizie su|dove si trova)\s+(un|una|uno|il|lo|la|i|gli|le|l\')?\s*', '', low).rstrip("?.!").strip() or msg
        return ("WEB_SEARCH", "IMAGE_PREVIEW", clean_q)

    # 3. Richieste visive pure
    if any(k in low for k in ["mostrami", "fammi vedere", "foto di", "immagine di", "immagini di", "com'è fatto", "com'è fatta"]):
        clean_q = re.sub(r'^(mostrami|fammi vedere|cerca foto di|cerca immagini di|foto di|immagine di)\s+(un|una|uno|il|lo|la|i|gli|le|l\')?\s*', '', low).rstrip("?.!").strip() or msg
        return ("IMAGE_SEARCH", "IMAGE_PREVIEW", clean_q)

    return None


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

    tool = "NONE"
    query = user_message
    screen_type = "NONE"
    screen_target = ""
    reasoning_text = "Analisi contestuale."

    # Step A: Controlla prima le regole deterministiche ad alta precisione
    rule_match = _detect_intent_by_rules(user_message)
    if rule_match:
        tool, screen_type, query = rule_match
        reasoning_text = f"Intent rilevato ({tool}): {query}"
    else:
        # Step B: Chiedi al router LLM per comandi complessi (Telegram, Contatti, Browser, ecc.)
        system_prompt = (
            "Sei il router di Peter OS. Scegli tool e schermata Visual HUD.\n"
            "Tool: YOUTUBE, APPLE_MUSIC, WEB_SEARCH, IMAGE_SEARCH, SEND_TELEGRAM, SEND_TELEGRAM_VOICE, NONE.\n"
            "HUD: MEDIA_PLAYER, IMAGE_PREVIEW, SEARCH_PREVIEW, PERSON_CARD, WEB_BROWSER, SYSTEM_BRIEF.\n"
            "Rispondi SOLO con JSON:\n"
            '{"reasoning": "Motivo", "tool": "...", "query": "...", "screen_type": "...", "screen_target": "..."}'
        )
        messages = [{"role": "system", "content": system_prompt}]
        if recent_context:
            messages.append({"role": "system", "content": f"Contesto:\n{truncate_text(recent_context, 350, from_end=True)}"})
        messages.append({"role": "user", "content": truncate_text(user_message, 600)})

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                res = await client.post(GROQ_URL, json={
                    "model": MODEL_ROUTER,
                    "messages": messages,
                    "temperature": 0.0
                }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})

                if res.status_code == 200:
                    raw_text = res.json()["choices"][0]["message"]["content"].strip()
                    if "{" in raw_text and "}" in raw_text:
                        raw_text = raw_text[raw_text.find("{"):raw_text.rfind("}")+1]
                        decision = json.loads(raw_text)
                        tool = decision.get("tool", "NONE").upper()
                        query = decision.get("query") or user_message
                        screen_type = decision.get("screen_type", "SYSTEM_BRIEF").upper()
                        screen_target = decision.get("screen_target", "")
                        reasoning_text = decision.get("reasoning", "Routing completato.")
        except Exception as e:
            print(f"Errore Router LLM: {e}")

    media_data = None
    screen_display = None
    telegram_sent = False

    # Step C: Esecuzione Tool e generazione payload HUD (l'HUD mostra SEMPRE qualcosa)
    try:
        if tool == "SEND_TELEGRAM":
            telegram_sent = await send_telegram_message(query)
            query_used = f"Telegram Text: '{query}'"
            screen_display = {
                "type": "SYSTEM_BRIEF",
                "title": "TELEGRAM DISPATCH",
                "subtitle": "Messaggio inviato" if telegram_sent else "Invio non riuscito (verifica chat_id)",
                "highlights": [query]
            }

        elif tool == "SEND_TELEGRAM_VOICE":
            telegram_sent = await send_telegram_voice_note(query)
            query_used = f"Telegram Voice: '{query}'"
            screen_display = {
                "type": "SYSTEM_BRIEF",
                "title": "TELEGRAM VOICE NOTE",
                "subtitle": "Nota vocale generata e inviata" if telegram_sent else "Errore invio vocale",
                "highlights": [query]
            }

        elif tool == "YOUTUBE" or screen_type == "MEDIA_PLAYER":
            if tool == "APPLE_MUSIC":
                media_data = search_apple_music(query)
                query_used = f"Apple Music: {query}"
                if media_data:
                    screen_display = {
                        "type": "MEDIA_PLAYER",
                        "source": "apple_music",
                        "title": media_data.get("title", query),
                        "embed_url": media_data.get("embed_url")
                    }
            else:
                media_data = search_youtube(query)
                query_used = f"YouTube: {query}"
                if media_data:
                    screen_display = {
                        "type": "MEDIA_PLAYER",
                        "source": "youtube",
                        "video_id": media_data.get("video_id"),
                        "title": media_data.get("title", query),
                        "author": media_data.get("author", ""),
                        "embed_url": media_data.get("embed_url"),
                        "watch_url": media_data.get("watch_url")
                    }
                else:
                    screen_display = {
                        "type": "SEARCH_PREVIEW",
                        "query": f"YouTube: {query}",
                        "content": f"Nessun video incorporabile trovato per '{query}'. Prova a specificare titolo e artista."
                    }

        elif tool in ("IMAGE_SEARCH", "WEB_SEARCH") or screen_type == "IMAGE_PREVIEW":
            if not web_content:
                web_content = search_web(query, max_results=4)
            img_res = search_image_result(query, max_results=5)
            query_used = f"{tool}: {query}"
            safe_web = truncate_text(web_content, 550)

            if img_res.get("image_url"):
                screen_display = {
                    "type": "IMAGE_PREVIEW",
                    "title": img_res.get("title") or query,
                    "image_url": img_res.get("image_url"),
                    "thumbnail_url": img_res.get("thumbnail_url"),
                    "source_url": img_res.get("source_url"),
                    "images": img_res.get("images", []),
                    "content": safe_web
                }
            else:
                screen_display = {
                    "type": "SEARCH_PREVIEW",
                    "query": query,
                    "content": safe_web or f"Nessun dato esterno trovato per '{query}'."
                }

        elif screen_type == "WEB_BROWSER" and screen_target.startswith("http"):
            screen_display = {"type": "WEB_BROWSER", "url": screen_target}

        elif screen_type == "PERSON_CARD" and screen_target:
            all_contacts = get_contacts()
            matched = next((c for c in all_contacts if screen_target.lower() in c['name'].lower()), None)
            screen_display = {
                "type": "PERSON_CARD",
                "person": matched or {"name": screen_target, "relation_type": "contatto", "notes": "Nessuna nota salvata"}
            }

        # Fallback intelligente: l'HUD non resta mai vuoto
        if not screen_display:
            now_label = datetime.now().strftime("%H:%M · %d/%m/%Y")
            screen_display = {
                "type": "SYSTEM_BRIEF",
                "title": "NEURAL CONTEXT HUD",
                "subtitle": f"ACTIVE SESSION · {now_label}",
                "highlights": [
                    f"Comando analizzato: {truncate_text(user_message, 90)}",
                    f"Routing: {reasoning_text}",
                    "Suggerimento: chiedi 'mostrami [oggetto]', 'chi è [persona]' o 'metti [brano] su YouTube'"
                ]
            }

    except Exception as e:
        print(f"Errore esecuzione Tool/HUD: {e}")

    return {
        "web": web_content,
        "media": media_data,
        "screen": screen_display,
        "query_used": query_used,
        "telegram_sent": telegram_sent,
        "reasoning": reasoning_text
    }


async def generate_peter_response(user_message: str, recent_context: str, long_term_facts: str, image_data_url: str = None) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca API KEY")

    is_mega_prompt = len(user_message) > 2500
    chat_message = user_message

    if is_mega_prompt:
        chat_message = (
            f"[SISTEMA INTERNO: Marco ha inviato un archivio testuale di {len(user_message)} caratteri. "
            "Rispondi brevemente confermando la ricezione e la suddivisione parallela nei 4 domini di memoria.]"
        )

    tool_exec = await model_1_route_tools(chat_message, recent_context)
    now_str = datetime.now().strftime("%A %d %B %Y, %H:%M CET")

    personality = get_personality_settings()
    current_tone = personality.get("tone", "Schietto, empatico, naturale, colto e ironico.")

    safe_long_term = truncate_text(long_term_facts, 2000)
    safe_recent_context = truncate_text(recent_context, 1200, from_end=True)
    safe_web_content = truncate_text(tool_exec["web"], 1400)

    hud_status_note = ""
    if tool_exec["screen"]:
        s_type = tool_exec["screen"].get("type", "")
        if s_type == "IMAGE_PREVIEW":
            hud_status_note = (
                "\n[SISTEMA HUD: Hai proiettato l'immagine nel Visual HUD a destra. "
                "NON descrivere mai dettagli visivi dell'immagine perché non la vedi; limita la risposta ai fatti verificati.]"
            )
        elif s_type == "MEDIA_PLAYER":
            vid_title = tool_exec["screen"].get("title", "")
            hud_status_note = (
                f"\n[SISTEMA HUD: Hai caricato nel player YouTube a destra il video '{vid_title}'. "
                "Conferma brevemente la riproduzione senza inventare date di uscita o dettagli non presenti nei dati.]"
            )

    system_prompt = (
        f"Sei Peter, l'IA personale di Marco.\n"
        f"DATA/ORA: {now_str}\n"
        f"- Tono: '{current_tone}'\n"
        "REGOLE ANTI-ALLUCINAZIONE E STILE:\n"
        "1. Rispondi in modo conciso, chiaro e naturale (massimo 3-4 frasi).\n"
        "2. Usa ESCLUSIVAMENTE i Web Data reali forniti qui sotto per date, biografie, prezzi o fatti recenti. Se un dato non è presente nei Web Data e non ne sei certo al 100%, dichiaralo senza indovinare.\n"
        "3. NON usare MAI tabelle Markdown (|), asterischi (**), cancelletti (#) o link [testo](url). Scrivi in testo pulito.\n"
        f"{hud_status_note}"
    )

    if safe_web_content:
        system_prompt += f"\nWeb Data reali (FONTE VERIFICATA):\n{safe_web_content}"
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
                "temperature": 0.15
            }, headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"})

            if res.status_code != 200:
                return {
                    "reply": f"Sovraccarico Neurale ({res.status_code}). Riprova tra un istante.",
                    "query_used": "", "media": None, "screen": tool_exec["screen"], "reasoning": f"> API Error {res.status_code}"
                }

            raw_reply = res.json()["choices"][0]["message"]["content"]
            return {
                "reply": clean_reply_text(raw_reply),
                "query_used": tool_exec["query_used"],
                "media": tool_exec["media"],
                "screen": tool_exec["screen"],
                "reasoning": f"> {tool_exec['reasoning']}"
            }
    except Exception as e:
        return {
            "reply": "Connessione neurale instabile. Riprova tra un istante.",
            "query_used": "", "media": None, "screen": tool_exec["screen"], "reasoning": f"> Errore: {str(e)}"
        }


# --- FUNZIONE WORKER PER IL CHUNKING PARALLELO CON ID DETERMINISTICI ---
async def process_chunk(chunk: str, model: str, index: int, image_data_url: str = None):
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
                                node_id = make_stable_id("fact", fact_text)
                                supabase.table("nodes").upsert({"id": node_id, "name": fact_text[:28], "type": "memory", "category": "memory", "notes": fact_text}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "memoria"}).execute()
                            except Exception:
                                pass

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
                            if supabase:
                                try:
                                    node_id = make_stable_id("contact", p_name)
                                    supabase.table("nodes").upsert({
                                        "id": node_id, "name": p_name, "type": "person",
                                        "category": p.get("relation_type", "amicizia"),
                                        "notes": p.get("notes", ""), "gender": p.get("gender", "sconosciuto"),
                                        "birth_year": p.get("birth_year"), "relation_type": p.get("relation_type", "neutrale")
                                    }).execute()
                                    supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": p.get("relation_type", "neutrale")}).execute()
                                except Exception:
                                    pass

                    if parsed.get("event_title") and parsed.get("event_title") != "NESSUNO":
                        ev_title = parsed.get("event_title")
                        save_event_entity(ev_title, parsed.get("event_desc", ""))
                        if supabase:
                            try:
                                node_id = make_stable_id("event", ev_title)
                                supabase.table("nodes").upsert({"id": node_id, "name": ev_title[:26], "type": "event", "category": "event", "notes": parsed.get("event_desc", "")}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "evento"}).execute()
                            except Exception:
                                pass

                    if parsed.get("interest_name") and parsed.get("interest_name") != "NESSUNO":
                        int_name = parsed.get("interest_name")
                        save_interest_entity(int_name, parsed.get("interest_desc", ""))
                        if supabase:
                            try:
                                node_id = make_stable_id("interest", int_name)
                                supabase.table("nodes").upsert({"id": node_id, "name": int_name[:26], "type": "interest", "category": "interest", "notes": parsed.get("interest_desc", "")}).execute()
                                supabase.table("edges").upsert({"source": "user_self", "target": node_id, "relation_type": "passione"}).execute()
                            except Exception:
                                pass
            else:
                print(f"Worker {model} fallito con status {res.status_code}")
    except Exception as e:
        print(f"Errore chunk worker {model}: {e}")


async def extract_and_save_facts(user_message: str, image_data_url: str = None):
    if not GROQ_API_KEY:
        return

    chunk_size = 2500
    chunks = [user_message[i:i+chunk_size] for i in range(0, len(user_message), chunk_size)]

    tasks = []
    for index, chunk in enumerate(chunks):
        if image_data_url and index == 0:
            assigned_model = MODEL_VISION
        else:
            assigned_model = WORKER_MODELS[index % len(WORKER_MODELS)]

        task = asyncio.create_task(process_chunk(chunk, assigned_model, index, image_data_url))
        tasks.append(task)

        if index > 0 and index % len(WORKER_MODELS) == 0:
            await asyncio.sleep(2)

    if tasks:
        await asyncio.gather(*tasks)
