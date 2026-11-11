from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = None
supabase_error_log = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_error_log = str(e)
else:
    supabase_error_log = "Credenziali Supabase incomplete"

def get_recent_memories(limit: int = 6) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("memories").select("content").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception as e:
        print(f"Errore memoria episodica: {e}")
    return ""

def get_long_term_facts(limit: int = 15) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("user_facts").select("fact").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([f"- {item['fact']}" for item in res.data])
    except Exception as e:
        print(f"Errore fatti lungo termine: {e}")
    return ""

def get_all_facts():
    if not supabase:
        return []
    try:
        res = supabase.table("user_facts").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"Errore lettura tutti i fatti: {e}")
        return []

def delete_fact_by_id(fact_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").delete().eq("id", fact_id).execute()
        return True
    except Exception as e:
        print(f"Errore eliminazione fatto: {e}")
        return False

def get_all_diaries():
    if not supabase:
        return []
    try:
        res = supabase.table("diaries").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        print(f"Errore lettura diari: {e}")
        return []

def get_graph_data():
    if not supabase:
        return {"nodes": [], "edges": []}
    try:
        nodes = supabase.table("nodes").select("*").execute().data or []
        edges = supabase.table("edges").select("*").execute().data or []
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"Errore lettura grafo: {e}")
        return {"nodes": [], "edges": []}

def save_episodic_memory(user_msg: str, peter_reply: str):
    if not supabase:
        return
    try:
        supabase.table("memories").insert([
            {"content": f"Utente: {user_msg}"},
            {"content": f"Peter: {peter_reply}"}
        ]).execute()
    except Exception as e:
        print(f"Errore salvataggio memoria: {e}")

def save_fact(fact_text: str):
    if not supabase:
        return
    try:
        supabase.table("user_facts").insert([{"fact": fact_text}]).execute()
    except Exception as e:
        print(f"Errore salvataggio fatto: {e}")
