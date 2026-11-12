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

def get_recent_memories(limit: int = 10) -> str:
    if not supabase: return ""
    try:
        res = supabase.table("memories").select("content").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception:
        pass
    return ""

def get_long_term_facts(limit: int = 30) -> str:
    if not supabase: return ""
    try:
        res = supabase.table("user_facts").select("*").order("created_at", desc=True).limit(limit).execute()
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
    if not supabase or not fact_text: return
    try:
        existing = supabase.table("user_facts").select("*").eq("fact", fact_text).execute()
        if not existing.data:
            supabase.table("user_facts").insert([{"fact": fact_text}]).execute()
    except Exception:
        pass

def save_contact_entity(name: str, category: str = "amicizia", notes: str = "", gender: str = "sconosciuto", birth_year: int = None, relation_type: str = "neutrale"):
    if not supabase or not name or name.upper() in ["NESSUNO", "MARCO", "BARBI", "MARCO BARBIERO TORRES"]: return
    try:
        res = supabase.table("contacts").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("contacts").insert([{
                "name": name,
                "category": category,
                "notes": notes,
                "gender": gender,
                "birth_year": birth_year,
                "relation_type": relation_type
            }]).execute()
        else:
            existing = res.data[0]
            updated_notes = (existing.get("notes", "") + f" | {notes}").strip(" |")
            supabase.table("contacts").update({
                "notes": updated_notes,
                "gender": gender if gender != "sconosciuto" else existing.get("gender"),
                "birth_year": birth_year if birth_year else existing.get("birth_year"),
                "relation_type": relation_type if relation_type != "neutrale" else existing.get("relation_type")
            }).eq("id", existing["id"]).execute()
    except Exception as e:
        print(f"Errore contatto: {e}")

def save_contacts_batch(contacts: list):
    if not supabase or not contacts: return
    try:
        supabase.table("contacts").insert(contacts).execute()
    except Exception as e:
        print(f"Errore batch contatti: {e}")

def get_contacts():
    if not supabase: return []
    try:
        return supabase.table("contacts").select("*").limit(50).execute().data or []
    except Exception:
        return []

def save_event_entity(title: str, description: str = ""):
    if not supabase or not title or title.upper() == "NESSUNO": return
    try:
        supabase.table("calendar_events").insert([{"title": title, "description": description, "start_time": "Programmato"}]).execute()
    except Exception:
        pass

def save_calendar_events_batch(events: list):
    if not supabase or not events: return
    try:
        supabase.table("calendar_events").insert(events).execute()
    except Exception as e:
        print(f"Errore batch eventi: {e}")

def save_interest_entity(name: str, description: str = ""):
    if not supabase or not name or name.upper() == "NESSUNO": return
    try:
        res = supabase.table("interests").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("interests").insert([{"name": name, "description": description}]).execute()
    except Exception:
        pass

def get_all_interests():
    if not supabase: return []
    try:
        return supabase.table("interests").select("*").execute().data or []
    except Exception:
        return []

def get_nexus_graph_data() -> dict:
    return calculate_galaxy_layout(supabase)

def get_personality_settings() -> dict:
    default_settings = {"tone": "Schietto, empatico, naturale, colto e ironico.", "initiative_level": "Alto"}
    if not supabase: return default_settings
    try:
        res = supabase.table("system_settings").select("value").eq("key", "personality").execute()
        if res.data: return res.data[0]["value"]
    except Exception:
        pass
    return default_settings

def save_personality_settings(settings: dict):
    if not supabase: return
    try:
        supabase.table("system_settings").upsert({"key": "personality", "value": settings}).execute()
    except Exception:
        pass

def save_telegram_chat_id(chat_id: int):
    if not supabase: return
    try:
        supabase.table("system_settings").upsert({"key": "last_telegram_chat_id", "value": str(chat_id)}).execute()
    except Exception:
        pass

def get_telegram_chat_id() -> str:
    if not supabase: return ""
    try:
        res = supabase.table("system_settings").select("value").eq("key", "last_telegram_chat_id").execute()
        if res.data: return res.data[0]["value"]
    except Exception:
        pass
    return ""

def wipe_table_data(table_type: str) -> bool:
    if not supabase: return False
    try:
        dummy_uuid = "00000000-0000-0000-0000-000000000000"
        if table_type == "memories":
            supabase.table("memories").delete().neq("id", dummy_uuid).execute()
            supabase.table("user_facts").delete().neq("id", dummy_uuid).execute()
            supabase.table("nodes").delete().eq("type", "memory").execute()
        elif table_type == "contacts":
            supabase.table("contacts").delete().neq("id", dummy_uuid).execute()
            supabase.table("nodes").delete().eq("type", "person").execute()
        elif table_type == "events":
            supabase.table("calendar_events").delete().neq("id", dummy_uuid).execute()
            supabase.table("nodes").delete().eq("type", "event").execute()
        elif table_type == "all":
            supabase.table("memories").delete().neq("id", dummy_uuid).execute()
            supabase.table("user_facts").delete().neq("id", dummy_uuid).execute()
            supabase.table("contacts").delete().neq("id", dummy_uuid).execute()
            supabase.table("calendar_events").delete().neq("id", dummy_uuid).execute()
            supabase.table("interests").delete().neq("id", dummy_uuid).execute()
            supabase.table("nodes").delete().neq("id", "user_self").execute()
            supabase.table("edges").delete().neq("id", dummy_uuid).execute()
        return True
    except Exception as e:
        print(f"Wipe error: {e}")
        return False
