from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY
from graph import calculate_galaxy_layout

supabase: Client = None
supabase_error_log = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_error_log = str(e)

def get_recent_memories(limit: int = 8) -> str:
    if not supabase: return ""
    try:
        res = supabase.table("memories").select("content").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception:
        pass
    return ""

def get_long_term_facts(limit: int = 25) -> str:
    if not supabase: return ""
    try:
        res = supabase.table("user_facts").select("fact").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([f"- {item['fact']}" for item in res.data])
    except Exception:
        pass
    return ""

def get_all_facts():
    if not supabase: return []
    try:
        res = supabase.table("user_facts").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def update_fact_by_id(fact_id: str, new_text: str) -> bool:
    if not supabase: return False
    try:
        supabase.table("user_facts").update({"fact": new_text}).eq("id", fact_id).execute()
        return True
    except Exception:
        return False

def delete_fact_by_id(fact_id: str) -> bool:
    if not supabase: return False
    try:
        supabase.table("user_facts").delete().eq("id", fact_id).execute()
        return True
    except Exception:
        return False

def save_episodic_memory(user_msg: str, peter_reply: str):
    if not supabase: return
    try:
        supabase.table("memories").insert([
            {"content": f"Marco: {user_msg}"},
            {"content": f"Peter: {peter_reply}"}
        ]).execute()
    except Exception:
        pass

def save_fact(fact_text: str):
    if not supabase: return
    try:
        supabase.table("user_facts").insert([{"fact": fact_text}]).execute()
    except Exception:
        pass

def save_contact_entity(name: str, category: str = "amicizia", notes: str = "", birthday: str = "", gender: str = "sconosciuto", birth_year: int = None, relation_type: str = "neutrale"):
    if not supabase or not name or name.upper() == "NESSUNO": return
    try:
        res = supabase.table("contacts").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("contacts").insert([{
                "name": name,
                "category": category,
                "notes": notes,
                "details": f"Data: {birthday}" if birthday else "Profilo Nexus",
                "gender":
