import time
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, List

from database import (
    supabase, supabase_error_log, get_recent_memories, 
    get_long_term_facts, get_all_facts, delete_fact_by_id, 
    save_episodic_memory, get_graph_data,
    add_or_update_node, add_edge, delete_node_by_id, delete_edge_by_id, sync_bulk_contacts
)
from llm import (
    generate_peter_response, 
    process_background_memory
)
from telegram_bot import process_telegram_update
from ui import get_dashboard_html

app = FastAPI(title="Peter OS Backend - JARVIS HUD")

class ChatRequest(BaseModel):
    message: str

class NodeRequest(BaseModel):
    name: str
    category: Optional[str] = "Amicizia"
    notes: Optional[str] = ""
    role: Optional[str] = ""
    phone: Optional[str] = ""
    email: Optional[str] = ""

class BulkSyncRequest(BaseModel):
    contacts: List[dict]

class EdgeRequest(BaseModel):
    source_id: str
    target_id: str
    relation_label: Optional[str] = "collegato"

start_time = time.time()

@app.get("/", response_class=HTMLResponse)
def root_dashboard():
    return get_dashboard_html()

@app.get("/api/telemetry")
def get_telemetry():
    """Endpoint per monitorare lo stato di sistema e la telemetria live."""
    uptime_seconds = int(time.time() - start_time)
    memories_count = len(get_recent_memories(limit=100).split("\n")) if get_recent_memories(limit=100) else 0
    facts_count = len(get_all_facts())
    graph_data = get_graph_data()

    return {
        "status": "ONLINE",
        "uptime_seconds": uptime_seconds,
        "supabase_connected": supabase is not None,
        "supabase_error": supabase_error_log,
        "models": {
            "router": "openai/gpt-oss-20b (Groq)",
            "core": "openai/gpt-oss-120b (Groq)",
            "fact_extractor": "qwen/qwen3.8-27b (Groq)"
        },
        "stats": {
            "episodic_memories": memories_count,
            "long_term_facts": facts_count,
            "nexus_nodes": len(graph_data.get("nodes", [])),
            "nexus_edges": len(graph_data.get("edges", []))
        }
    }

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

# === NEXUS CONTACTS VAULT ENDPOINTS ===
@app.get("/api/graph")
def api_get_graph():
    return get_graph_data()

@app.post("/api/graph/node")
def api_add_node(req: NodeRequest):
    node = add_or_update_node(req.name, req.category, req.notes, req.role, req.phone, req.email)
    if not node:
        raise HTTPException(status_code=500, detail="Impossibile inserire la persona")
    return {"status": "ok", "node": node}

@app.post("/api/graph/sync")
def api_sync_contacts(req: BulkSyncRequest):
    synced_count = sync_bulk_contacts(req.contacts)
    return {"status": "ok", "synced_count": synced_count}

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

# === CHAT & TELEGRAM WEBHOOK ===
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
