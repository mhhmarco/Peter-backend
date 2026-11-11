from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from database import (
    supabase, supabase_error_log, get_recent_memories, 
    get_long_term_facts, get_all_facts, delete_fact_by_id, 
    save_episodic_memory
)
from llm import generate_peter_response, extract_and_save_facts
from telegram_bot import process_telegram_update
from ui import get_dashboard_html

app = FastAPI(title="Peter OS Backend")

class ChatRequest(BaseModel):
    message: str

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

@app.get("/api/facts")
def api_get_facts():
    return get_all_facts()

@app.delete("/api/facts/{fact_id}")
def api_delete_fact(fact_id: str):
    success = delete_fact_by_id(fact_id)
    if not success:
        raise HTTPException(status_code=500, detail="Impossibile eliminare il fatto")
    return {"status": "deleted"}

@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update = await request.json()
    await process_telegram_update(update)
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    recent_context = get_recent_memories(limit=8)
    long_term_facts = get_long_term_facts(limit=15)

    result = await generate_peter_response(req.message, recent_context, long_term_facts)
    reply = result["reply"]
    query_used = result.get("query_used")
    media = result.get("media")

    save_episodic_memory(req.message, reply)
    await extract_and_save_facts(req.message)

    return {"reply": reply, "query_used": query_used, "media": media}
