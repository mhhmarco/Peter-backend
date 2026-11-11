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

def get_long_term_facts(limit: int = 20) -> str:
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

def update_fact_by_id(fact_id: str, new_text: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").update({"fact": new_text}).eq("id", fact_id).execute()
        return True
    except Exception as e:
        print(f"Errore aggiornamento fatto: {e}")
        return False

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

def save_telegram_chat_id(chat_id: int):
    if not supabase:
        return
    try:
        supabase.table("system_settings").upsert({"key": "last_telegram_chat_id", "value": str(chat_id)}).execute()
    except Exception:
        pass

def get_telegram_chat_id() -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("system_settings").select("value").eq("key", "last_telegram_chat_id").execute()
        if res.data:
            return res.data[0]["value"]
    except Exception:
        pass
    return ""

def save_contact_entity(name: str, category: str = "amicizia", notes: str = "", event_title: str = ""):
    if not supabase:
        return
    try:
        res = supabase.table("contacts").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("contacts").insert([{
                "name": name,
                "category": category,
                "notes": notes,
                "details": f"Evento: {event_title}" if event_title else ""
            }]).execute()
        elif event_title or notes:
            existing = res.data[0]
            updated_notes = (existing.get("notes", "") + f" | {notes}").strip(" |")
            supabase.table("contacts").update({"notes": updated_notes}).eq("id", existing["id"]).execute()
    except Exception as e:
        print(f"Errore salvataggio entità Nexus: {e}")

def get_nexus_graph_data() -> dict:
    nodes = [{"id": "user_self", "name": "Marco", "category": "self", "x": 0, "y": 0, "z": 0, "notes": "Admin Peter OS"}]
    edges = []
    if not supabase:
        return {"nodes": nodes, "edges": edges}

    try:
        contacts_res = supabase.table("contacts").select("*").execute()
        contacts = contacts_res.data or []
        import math
        for idx, c in enumerate(contacts):
            node_id = f"contact_{c.get('id', idx)}"
            cat = c.get("category", "amicizia").lower()
            angle = (idx / max(len(contacts), 1)) * 2 * math.pi
            radius = 140 if cat == "famiglia" else 180
            nodes.append({
                "id": node_id,
                "name": c.get("name", "Persona"),
                "category": cat,
                "x": math.cos(angle) * radius,
                "y": math.sin(angle) * radius * 0.5,
                "z": math.sin(angle) * radius,
                "notes": c.get("notes", ""),
                "events": [c.get("details")] if c.get("details") else []
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception as e:
        print(f"Errore Nexus Graph: {e}")

    return {"nodes": nodes, "edges": edges}

def save_contacts_batch(contacts: list):
    if not supabase or not contacts:
        return
    try:
        supabase.table("contacts").insert(contacts).execute()
    except Exception:
        pass

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
    except Exception:
        pass

def get_personality_settings() -> dict:
    default_settings = {
        "tone": "Schietto, empatico, naturale, colto e ironico.",
        "initiative_level": "Alto (Suggerimenti proattivi)",
        "custom_instructions": "Tratta Marco come un amico fidato alla pari."
    }
    if not supabase:
        return default_settings
    try:
        res = supabase.table("system_settings").select("value").eq("key", "personality").execute()
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
    except Exception:
        pass
