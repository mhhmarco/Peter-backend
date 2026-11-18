import re
import hashlib
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


def make_stable_id(prefix: str, text: str) -> str:
    """Genera un ID deterministico identico tra riavvii diversi del server Render."""
    normalized = re.sub(r'\s+', ' ', (text or '').strip().lower())
    digest = hashlib.sha1(normalized.encode('utf-8')).hexdigest()[:14]
    return f"{prefix}_{digest}"


def get_telegram_chat_id():
    if not supabase:
        return None
    try:
        res = (
            supabase.table("system_settings")
            .select("value")
            .eq("key", "global_config")
            .execute()
        )
        if not res.data:
            return None
        settings = res.data[0].get("value") or {}
        return settings.get("telegram_chat_id")
    except Exception as e:
        print(f"Errore lettura Telegram chat ID: {e}")
        return None


def save_telegram_chat_id(chat_id):
    if not supabase or chat_id is None:
        return
    try:
        res = (
            supabase.table("system_settings")
            .select("value")
            .eq("key", "global_config")
            .execute()
        )
        settings = res.data[0].get("value") or {} if res.data else {}
        settings["telegram_chat_id"] = str(chat_id)
        supabase.table("system_settings").upsert({
            "key": "global_config",
            "value": settings
        }).execute()
    except Exception as e:
        print(f"Errore salvataggio Telegram chat ID: {e}")


def get_personality_settings() -> dict:
    default = {
        "timezone": "Europe/Rome",
        "public_calendar_url": "",
        "tone": "Schietto, empatico, naturale, colto e ironico."
    }
    if not supabase:
        return default
    try:
        res = (
            supabase.table("system_settings")
            .select("value")
            .eq("key", "global_config")
            .execute()
        )
        if res.data:
            return {**default, **res.data[0]["value"]}
    except Exception:
        pass
    return default


def save_personality_settings(settings: dict):
    if not supabase:
        return
    try:
        current = get_personality_settings()
        updated = {**current, **settings}
        supabase.table("system_settings").upsert({
            "key": "global_config",
            "value": updated
        }).execute()
    except Exception as e:
        print(f"Error saving settings: {e}")


def save_contact_entity(
    name: str,
    category: str = "amicizia",
    notes: str = "",
    gender: str = "sconosciuto",
    birth_year: int = None,
    relation_type: str = "neutrale"
):
    if not supabase or not name:
        return
    if name.upper() in ["NESSUNO", "MARCO", "BARBI", "MARCO BARBIERO TORRES"]:
        return

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
            old_notes = existing.get("notes", "")
            updated_notes = old_notes if notes in old_notes else f"{old_notes} | {notes}".strip(" |")
            supabase.table("contacts").update({
                "notes": updated_notes,
                "gender": gender if gender != "sconosciuto" else existing.get("gender"),
                "birth_year": birth_year if birth_year else existing.get("birth_year"),
                "relation_type": relation_type if relation_type != "neutrale" else existing.get("relation_type")
            }).eq("id", existing["id"]).execute()
    except Exception as e:
        print(f"Errore contatto: {e}")


def save_contacts_batch(contacts: list):
    if not supabase or not contacts:
        return
    for contact in contacts:
        save_contact_entity(
            name=contact.get("name"),
            category=contact.get("category", "amicizia"),
            notes=contact.get("notes", ""),
            gender=contact.get("gender", "sconosciuto"),
            birth_year=contact.get("birth_year"),
            relation_type=contact.get("relation_type", "neutrale")
        )


def save_event_entity(title: str, description: str = "", start_time: str = None):
    if not supabase or not title:
        return
    try:
        supabase.table("calendar_events").upsert(
            {
                "title": title,
                "description": description,
                "start_time": start_time
            },
            on_conflict="title,start_time"
        ).execute()
    except Exception as e:
        print(f"Errore salvataggio evento: {e}")


def save_calendar_events_batch(events: list):
    if not supabase or not events:
        return
    for event in events:
        save_event_entity(
            title=event.get("title"),
            description=event.get("description", ""),
            start_time=event.get("start_time")
        )


def save_interest_entity(name: str, category: str = "generale", notes: str = ""):
    if not supabase or not name:
        return
    try:
        res = supabase.table("interests").select("*").ilike("name", name).execute()
        if not res.data:
            supabase.table("interests").insert([{
                "name": name,
                "category": category,
                "notes": notes
            }]).execute()
        else:
            existing = res.data[0]
            old_notes = existing.get("notes", "")
            updated_notes = old_notes if notes in old_notes else f"{old_notes} | {notes}".strip(" |")
            supabase.table("interests").update({"notes": updated_notes}).eq("id", existing["id"]).execute()
    except Exception as e:
        print(f"Errore salvataggio interesse: {e}")


def get_all_interests(limit: int = 40) -> list:
    if not supabase:
        return []
    try:
        res = supabase.table("interests").select("*").limit(limit).execute()
        return res.data or []
    except Exception as e:
        print(f"Errore lettura interessi: {e}")
        return []


def get_all_events(limit: int = 40) -> list:
    if not supabase:
        return []
    try:
        res = supabase.table("calendar_events").select("*").limit(limit).execute()
        return res.data or []
    except Exception as e:
        print(f"Errore lettura eventi: {e}")
        return []


def merge_contact_aliases(alias_name: str, target_name: str) -> bool:
    if not supabase:
        return False
    try:
        alias_res = supabase.table("contacts").select("*").ilike("name", alias_name).execute()
        target_res = supabase.table("contacts").select("*").ilike("name", target_name).execute()
        if not alias_res.data or not target_res.data:
            return False

        alias_contact = alias_res.data[0]
        target_contact = target_res.data[0]
        merged_notes = (
            f"{target_contact.get('notes', '')} | "
            f"Unificato con alias: {alias_contact['name']} ({alias_contact.get('notes', '')})"
        ).strip(" |")

        supabase.table("contacts").update({"notes": merged_notes}).eq("id", target_contact["id"]).execute()
        supabase.table("contacts").delete().eq("id", alias_contact["id"]).execute()

        alias_node_id = make_stable_id("contact", alias_contact["name"])
        supabase.table("nodes").delete().eq("id", alias_node_id).execute()
        supabase.table("edges").delete().eq("source", alias_node_id).execute()
        supabase.table("edges").delete().eq("target", alias_node_id).execute()
        return True
    except Exception as e:
        print(f"Errore merge alias: {e}")
        return False


def get_recent_memories(limit: int = 10) -> str:
    if not supabase:
        return ""
    try:
        res = (
            supabase.table("memories")
            .select("content")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception:
        pass
    return ""


def get_long_term_facts(limit: int = 30) -> str:
    if not supabase:
        return ""
    try:
        res = (
            supabase.table("user_facts")
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        if res.data:
            return "\n".join([f"- {item['fact']}" for item in res.data])
    except Exception:
        pass
    return ""


def get_structured_memory_overview() -> dict:
    """Restituisce la memoria suddivisa nei 4 domini cognitivi per la UI iOS 27."""
    if not supabase:
        return {
            "connected": False,
            "stats": {"semantic": 0, "social": 0, "temporal": 0, "episodic": 0},
            "semantic": [],
            "social": [],
            "temporal": [],
            "episodic": []
        }
    try:
        facts = supabase.table("user_facts").select("*").order("created_at", desc=True).limit(50).execute().data or []
        contacts = supabase.table("contacts").select("*").limit(50).execute().data or []
        events = supabase.table("calendar_events").select("*").limit(30).execute().data or []
        interests = supabase.table("interests").select("*").limit(30).execute().data or []
        episodes = supabase.table("memories").select("*").order("created_at", desc=True).limit(25).execute().data or []

        temporal = [
            {"id": f"ev_{e.get('id')}", "kind": "event", "title": e.get("title", ""), "detail": e.get("description", ""), "when": e.get("start_time") or ""}
            for e in events
        ] + [
            {"id": f"int_{i.get('id')}", "kind": "interest", "title": i.get("name", ""), "detail": i.get("notes", ""), "when": i.get("category", "interesse")}
            for i in interests
        ]

        return {
            "connected": True,
            "stats": {
                "semantic": len(facts),
                "social": len(contacts),
                "temporal": len(temporal),
                "episodic": len(episodes)
            },
            "semantic": facts,
            "social": contacts,
            "temporal": temporal,
            "episodic": episodes
        }
    except Exception as e:
        print(f"Errore lettura memoria strutturata: {e}")
        return {
            "connected": False,
            "stats": {"semantic": 0, "social": 0, "temporal": 0, "episodic": 0},
            "semantic": [],
            "social": [],
            "temporal": [],
            "episodic": []
        }


def save_episodic_memory(content: str, reply: str = None):
    if not supabase or not content:
        return
    memory_content = f"Utente: {content}\nPeter: {reply}" if reply is not None else content
    try:
        supabase.table("memories").insert({"content": memory_content}).execute()
    except Exception as e:
        print(f"Errore salvataggio memoria episodica: {e}")


def save_fact(fact_text: str):
    if not supabase or not fact_text:
        return
    try:
        existing = supabase.table("user_facts").select("id").ilike("fact", fact_text.strip()).execute()
        if not existing.data:
            supabase.table("user_facts").insert({"fact": fact_text.strip()}).execute()
    except Exception as e:
        print(f"Errore salvataggio fact: {e}")


def delete_fact_by_id(fact_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").delete().eq("id", fact_id).execute()
        return True
    except Exception:
        return False


def update_fact_by_id(fact_id: str, new_text: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").update({"fact": new_text}).eq("id", fact_id).execute()
        return True
    except Exception:
        return False


def get_contacts():
    if not supabase:
        return []
    try:
        return supabase.table("contacts").select("*").limit(60).execute().data or []
    except Exception:
        return []


def get_nexus_graph_data() -> dict:
    return calculate_galaxy_layout(supabase)


def wipe_table_data(table_type: str) -> bool:
    if not supabase:
        return False
    try:
        dummy_uuid = "00000000-0000-0000-0000-000000000000"
        if table_type == "memories":
            supabase.table("memories").delete().neq("id", dummy_uuid).execute()
            supabase.table("user_facts").delete().neq("id", dummy_uuid).execute()
        elif table_type == "contacts":
            supabase.table("contacts").delete().neq("id", dummy_uuid).execute()
        elif table_type == "events":
            supabase.table("calendar_events").delete().neq("id", dummy_uuid).execute()
        elif table_type == "all":
            supabase.table("memories").delete().neq("id", dummy_uuid).execute()
            supabase.table("user_facts").delete().neq("id", dummy_uuid).execute()
            supabase.table("contacts").delete().neq("id", dummy_uuid).execute()
            supabase.table("calendar_events").delete().neq("id", dummy_uuid).execute()
            supabase.table("interests").delete().neq("id", dummy_uuid).execute()
            supabase.table("nodes").delete().neq("id", "user_self").execute()
            supabase.table("edges").delete().neq("id", dummy_uuid).execute()
        return True
    except Exception:
        return False
