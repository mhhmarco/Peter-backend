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

def get_recent_memories(limit: int = 8) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("memories").select("content").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception:
        pass
    return ""

def get_long_term_facts(limit: int = 15) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("user_facts").select("fact").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([f"- {item['fact']}" for item in res.data])
    except Exception:
        pass
    return ""

def get_all_facts():
    if not supabase:
        return []
    try:
        res = supabase.table("user_facts").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception:
        return []

def delete_fact_by_id(fact_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").delete().eq("id", fact_id).execute()
        return True
    except Exception:
        return False

def save_episodic_memory(user_msg: str, peter_reply: str):
    if not supabase:
        return
    try:
        supabase.table("memories").insert([
            {"content": f"Marco: {user_msg}"},
            {"content": f"Peter: {peter_reply}"}
        ]).execute()
    except Exception:
        pass

def save_fact(fact_text: str):
    if not supabase:
        return
    try:
        supabase.table("user_facts").insert([{"fact": fact_text}]).execute()
    except Exception:
        pass

# GESTIONE CONTATTI & CALENDARIO
def save_contacts_batch(contacts: list):
    if not supabase or not contacts:
        return
    try:
        supabase.table("contacts").insert(contacts).execute()
    except Exception as e:
        print(f"Errore salvataggio batch contatti: {e}")

def get_contacts():
    if not supabase:
        return []
    try:
        res = supabase.table("contacts").select("*").limit(50).execute()
        return res.data or []
    except Exception:
        return []

def save_calendar_events_batch(events: list):
    if not supabase or not events:
        return
    try:
        supabase.table("calendar_events").insert(events).execute()
    except Exception as e:
        print(f"Errore salvataggio batch calendari: {e}")

def get_calendar_events():
    if not supabase:
        return []
    try:
        res = supabase.table("calendar_events").select("*").limit(30).execute()
        return res.data or []
    except Exception:
        return []

# PERSONALITY MATRIX
def get_personality_settings() -> dict:
    default_settings = {
        "tone": "Schietto, empatico, naturale, colto e ironico.",
        "initiative_level": "Alto (Suggerimenti proattivi)",
        "custom_instructions": "Tratta Marco come un amico fidato. Fai riferimenti espliciti agli elementi visibili sullo Schermo HUD quando pertinenti."
    }
    if not supabase:
        return default_settings
    try:
        res = supabase.table("system_settings").select("*").eq("key", "personality").execute()
        if res.data:
            return res.data[0]["value"]
    except Exception:
        pass
    return default_settings

def save_personality_settings(settings: dict):
    if not supabase:
        return
    try:
        supabase.table("system_settings").upsert({"key": "personality", "value": settings}).execute()
    except Exception as e:
        print(f"Errore salvataggio personalità: {e}")
