from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional

from database import (
    supabase, supabase_error_log, get_recent_memories, 
    get_long_term_facts, get_all_facts, delete_fact_by_id, 
    save_episodic_memory, get_graph_data, get_recent_diaries,
    add_or_update_node, add_edge, delete_node_by_id, delete_edge_by_id
)
from llm import (
    generate_peter_response, 
    process_background_memory, 
    generate_daily_reflection
)
from telegram_bot import process_telegram_update
from ui import get_dashboard_html

app = FastAPI(title="Peter OS Backend")

class ChatRequest(BaseModel):
    message: str

class NodeRequest(BaseModel):
    name: str
    category: Optional[str] = "Amicizia"
    notes: Optional[str] = ""

class EdgeRequest(BaseModel):
    source_id: str
    target_id: str
    relation_label: Optional[str] = "collegato"

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

# === ENDPOINT GRAFO NEXUS 3D ===
@app.get("/api/graph")
def api_get_graph():
    return get_graph_data()

@app.post("/api/graph/node")
def api_add_node(req: NodeRequest):
    node = add_or_update_node(req.name, req.category, req.notes)
    if not node:
        raise HTTPException(status_code=500, detail="Impossibile inserire la persona")
    return {"status": "ok", "node": node}

@app.post("/api/graph/edge")
def api_add_edge(req: EdgeRequest):
    edge = add_edge(req.source_id, req.target_id, req.relation_label)
    if not edge:
        raise HTTPException(status_code=500, detail="Impossibile inserire il legame")
    return {"status": "ok", "edge": edge}

@app.delete("/api/graph/node/{node_id}")
def api_delete_node(node_id: str):
    success = delete_node_by_id(node_id)
    if not success:
        raise HTTPException(status_code=500, detail="Errore eliminazione persona")
    return {"status": "deleted"}

@app.delete("/api/graph/edge/{edge_id}")
def api_delete_edge(edge_id: str):
    success = delete_edge_by_id(edge_id)
    if not success:
        raise HTTPException(status_code=500, detail="Errore eliminazione legame")
    return {"status": "deleted"}

# === ENDPOINT DIARI ===
@app.get("/api/diaries")
def api_get_diaries():
    return get_recent_diaries()

@app.post("/api/diaries/generate")
async def api_generate_diary():
    entry = await generate_daily_reflection()
    if not entry:
        raise HTTPException(status_code=500, detail="Impossibile generare il diario")
    return {"status": "success", "entry": entry}

# === WEBHOOK TELEGRAM & CHAT ===
@app.post("/telegram/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    update = await request.json()
    await process_telegram_update(update, background_tasks)
    return {"status": "ok"}

@app.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    recent_context = get_recent_memories(limit=8)
    long_term_facts = get_long_term_facts(limit=15)

    result = await generate_peter_response(req.message, recent_context, long_term_facts)
    reply = result["reply"]
    query_used = result.get("query_used")
    media = result.get("media")

    save_episodic_memory(req.message, reply)
    background_tasks.add_task(process_background_memory, req.message)

    return {"reply": reply, "query_used": query_used, "media": media}
