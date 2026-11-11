from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

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

def save_contact_entity(name: str, category: str = "amicizia", notes: str = "", birthday: str = ""):
    if not supabase or not name or name.upper() == "NESSUNO": return
    try:
        res = supabase.table("contacts").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("contacts").insert([{
                "name": name,
                "category": category,
                "notes": notes,
                "details": f"Compleanno/Data: {birthday}" if birthday else "Nessun dettaglio aggiuntivo"
            }]).execute()
        else:
            existing = res.data[0]
            updated_notes = (existing.get("notes", "") + f" | {notes}").strip(" |")
            supabase.table("contacts").update({"notes": updated_notes}).eq("id", existing["id"]).execute()
    except Exception as e:
        print(f"Errore salvataggio contatto: {e}")

def save_contacts_batch(contacts: list):
    if not supabase or not contacts: return
    try:
        supabase.table("contacts").insert(contacts).execute()
    except Exception as e:
        print(f"Errore batch contatti: {e}")

def get_contacts():
    if not supabase: return []
    try:
        res = supabase.table("contacts").select("*").limit(50).execute()
        return res.data or []
    except Exception:
        return []

def save_event_entity(title: str, description: str = ""):
    if not supabase or not title or title.upper() == "NESSUNO": return
    try:
        supabase.table("calendar_events").insert([{
            "title": title,
            "description": description,
            "start_time": "Programmato"
        }]).execute()
    except Exception as e:
        print(f"Errore salvataggio evento: {e}")

def save_calendar_events_batch(events: list):
    if not supabase or not events: return
    try:
        supabase.table("calendar_events").insert(events).execute()
    except Exception as e:
        print(f"Errore batch eventi: {e}")

def get_nexus_graph_data() -> dict:
    nodes = [{"id": "user_self", "name": "Marco (Tu)", "category": "core", "type": "core", "x": 0, "y": 0, "z": 0, "notes": "Admin Peter OS - Centro neurale principale"}]
    edges = []
    if not supabase: return {"nodes": nodes, "edges": edges}

    import math

    try:
        contacts = supabase.table("contacts").select("*").execute().data or []
        for idx, c in enumerate(contacts):
            node_id = f"contact_{c.get('id', idx)}"
            angle = (idx / max(len(contacts), 1)) * 2 * math.pi
            nodes.append({
                "id": node_id, "name": c.get("name", "Persona"), "category": c.get("category", "amicizia"),
                "type": "person", "x": math.cos(angle) * 220, "y": math.sin(angle * 2) * 80, "z": math.sin(angle) * 220,
                "notes": c.get("notes", "Nessuna nota"), "details": c.get("details", "")
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    try:
        facts = supabase.table("user_facts").select("*").limit(35).execute().data or []
        for idx, f in enumerate(facts):
            node_id = f"fact_{f.get('id', idx)}"
            angle = (idx / max(len(facts), 1)) * 2 * math.pi + 0.7
            nodes.append({
                "id": node_id, "name": f.get("fact", "")[:26] + "...", "category": "memory",
                "type": "memory", "x": math.cos(angle) * 360, "y": ((idx % 3) - 1) * 120, "z": math.sin(angle) * 360,
                "notes": f.get("fact", ""), "details": f"Registrato: {f.get('created_at', '')[:10]}"
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    try:
        events = supabase.table("calendar_events").select("*").limit(20).execute().data or []
        for idx, e in enumerate(events):
            node_id = f"event_{e.get('id', idx)}"
            angle = (idx / max(len(events), 1)) * 2 * math.pi + 1.4
            nodes.append({
                "id": node_id, "name": e.get("title", "Evento")[:24], "category": "event",
                "type": "event", "x": math.cos(angle) * 480, "y": ((idx % 2) * 160) - 80, "z": math.sin(angle) * 480,
                "notes": e.get("description", "Nessuna descrizione"), "details": f"Stato: {e.get('start_time', '')}"
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}

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
