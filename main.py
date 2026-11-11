import tempfile
import os
import httpx
import edge_tts
from fastapi import FastAPI, HTTPException, Request, UploadFile, File, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from database import (
    supabase, supabase_error_log, get_recent_memories, 
    get_long_term_facts, get_all_facts, delete_fact_by_id, 
    save_episodic_memory, save_contacts_batch, get_contacts,
    save_calendar_events_batch, get_personality_settings, save_personality_settings,
    get_nexus_graph_data
)
from llm import generate_peter_response, extract_and_save_facts
from telegram_bot import process_telegram_update
from ui import get_dashboard_html
from importer import parse_vcard, fetch_and_parse_ical
from config import GROQ_API_KEY

app = FastAPI(title="Peter OS Backend")

class ChatRequest(BaseModel):
    message: str

class ICalRequest(BaseModel):
    url: str

@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    return get_dashboard_html()

@app.get("/memories")
def check_memories():
    if not supabase:
        return {"connected": False, "error": "Supabase non connesso", "dettaglio": supabase_error_log}
    try:
        res_mem = supabase.table("memories").select("*").order("created_at", desc=True).limit(10).execute()
        res_facts = supabase.table("user_facts").select("*").order("created_at", desc=True).limit(15).execute()
        return {
            "connected": True,
            "episodic_memories": res_mem.data,
            "long_term_facts": res_facts.data
        }
    except Exception as e:
        return {"connected": False, "error": f"Errore lettura: {str(e)}"}

@app.get("/api/nexus")
def api_get_nexus():
    """Endpoint per la Mappa 3D Nexus Interattiva."""
    return get_nexus_graph_data()

@app.get("/api/contacts")
def api_get_contacts():
    return get_contacts()

@app.post("/api/import/vcf")
async def import_vcf(file: UploadFile = File(...)):
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")
    contacts = parse_vcard(text)
    if contacts:
        save_contacts_batch(contacts)
        return {"status": "success", "count": len(contacts)}
    return {"status": "no_contacts_found"}

@app.post("/api/import/ical")
async def import_ical(req: ICalRequest):
    events = await fetch_and_parse_ical(req.url)
    if events:
        save_calendar_events_batch(events)
        return {"status": "success", "count": len(events)}
    return {"status": "no_events_found"}

@app.get("/api/personality")
def api_get_personality():
    return get_personality_settings()

@app.post("/api/personality")
def api_save_personality(settings: dict):
    save_personality_settings(settings)
    return {"status": "updated"}

@app.delete("/api/facts/{fact_id}")
def api_delete_fact(fact_id: str):
    success = delete_fact_by_id(fact_id)
    if not success:
        raise HTTPException(status_code=500, detail="Impossibile eliminare il fatto")
    return {"status": "deleted"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()
    background_tasks.add_task(process_telegram_update, update)
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    recent_context = get_recent_memories(limit=8)
    long_term_facts = get_long_term_facts(limit=15)

    result = await generate_peter_response(req.message, recent_context, long_term_facts)
    reply = result["reply"]
    query_used = result.get("query_used")
    media = result.get("media")
    screen = result.get("screen")

    save_episodic_memory(req.message, reply)
    
    # Esecuzione asincrona background per velocità istantanea
    background_tasks.add_task(extract_and_save_facts, req.message)

    return {"reply": reply, "query_used": query_used, "media": media, "screen": screen}

@app.websocket("/ws/voice")
async def websocket_voice_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            audio_bytes = await websocket.receive_bytes()
            if not audio_bytes:
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes)
                tmp_path = tmp.name

            user_text = ""
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    with open(tmp_path, "rb") as f:
                        res = await client.post(
                            "https://api.groq.com/openai/v1/audio/transcriptions",
                            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                            files={"file": ("audio.wav", f, "audio/wav")},
                            data={"model": "whisper-large-v3-turbo", "language": "it"}
                        )
                        if res.status_code == 200:
                            user_text = res.json().get("text", "").strip()
            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

            if not user_text:
                continue

            recent_context = get_recent_memories(limit=6)
            long_term_facts = get_long_term_facts(limit=10)
            llm_res = await generate_peter_response(user_text, recent_context, long_term_facts)
            reply_text = llm_res["reply"]
            screen_data = llm_res.get("screen")

            save_episodic_memory(user_text, reply_text)
            await extract_and_save_facts(user_text)

            tts = edge_tts.Communicate(reply_text, voice="it-IT-DiegoNeural")
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_mp3:
                await tts.save(tmp_mp3.name)
                with open(tmp_mp3.name, "rb") as f_mp3:
                    audio_out = f_mp3.read()
                os.remove(tmp_mp3.name)

            await websocket.send_json({
                "user_text": user_text,
                "reply_text": reply_text,
                "screen": screen_data
            })
            await websocket.send_bytes(audio_out)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"Errore WebSocket Voice: {e}")
