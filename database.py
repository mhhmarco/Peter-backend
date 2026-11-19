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
    relation_type: str = "neutrale",
    birthday: str = None,
    photo_url: str = None
):
    """Salva o aggiorna un contatto in Supabase includendo compleanno, foto e note relazionali."""
    if not supabase or not name:
        return
    clean_name = name.strip()
    if len(clean_name) > 45 or clean_name.upper() in ["NESSUNO", "MARCO", "BARBI", "MARCO BARBIERO TORRES", "UTENTE", "SCONOSCIUTO"]:
        return

    try:
        res = supabase.table("contacts").select("*").ilike("name", clean_name).execute()
        if not res.data:
            payload = {
                "name": clean_name,
                "category": category,
                "notes": notes,
                "gender": gender,
                "birth_year": birth_year,
                "relation_type": relation_type
            }
            if birthday:
                payload["birthday"] = birthday
            if photo_url:
                payload["photo_url"] = photo_url
            try:
                supabase.table("contacts").insert([payload]).execute()
            except Exception:
                # Fallback resiliente se le colonne opzionali birthday/photo_url non esistono ancora nello schema SQL
                payload.pop("birthday", None)
                payload.pop("photo_url", None)
                supabase.table("contacts").insert([payload]).execute()
        else:
            existing = res.data[0]
            old_notes = existing.get("notes", "")
            updated_notes = old_notes if (not notes or notes in old_notes) else f"{old_notes} | {notes}".strip(" |")
            update_payload = {
                "notes": updated_notes,
                "gender": gender if gender != "sconosciuto" else existing.get("gender"),
                "birth_year": birth_year if birth_year else existing.get("birth_year"),
                "relation_type": relation_type if relation_type != "neutrale" else existing.get("relation_type"),
                "category": category if category != "amicizia" else existing.get("category", category)
            }
            if birthday:
                update_payload["birthday"] = birthday
            if photo_url:
                update_payload["photo_url"] = photo_url
            try:
                supabase.table("contacts").update(update_payload).eq("id", existing["id"]).execute()
            except Exception:
                # Fallback se le colonne opzionali non sono presenti nella tabella contacts
                update_payload.pop("birthday", None)
                update_payload.pop("photo_url", None)
                supabase.table("contacts").update(update_payload).eq("id", existing["id"]).execute()
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
            relation_type=contact.get("relation_type", "neutrale"),
            birthday=contact.get("birthday"),
            photo_url=contact.get("photo_url")
        )


def delete_person_node(node_id: str) -> bool:
    """Elimina un nodo persona (e eventuali duplicati con lo stesso nome) da nodes, edges e contacts."""
    if not supabase or not node_id or node_id == "user_self":
        return False
    try:
        node_res = supabase.table("nodes").select("*").eq("id", node_id).execute()
        target_name = node_res.data[0].get("name") if node_res.data else None

        # Rimuove il nodo e tutti i suoi archi associati
        supabase.table("edges").delete().eq("source", node_id).execute()
        supabase.table("edges").delete().eq("target", node_id).execute()
        supabase.table("nodes").delete().eq("id", node_id).execute()

        # Rimuove anche eventuali duplicati con lo stesso nome e il record in contacts
        if target_name:
            dups = supabase.table("nodes").select("id").ilike("name", target_name).execute().data or []
            for d in dups:
                did = d.get("id")
                if did and did != "user_self":
                    supabase.table("edges").delete().eq("source", did).execute()
                    supabase.table("edges").delete().eq("target", did).execute()
                    supabase.table("nodes").delete().eq("id", did).execute()
            supabase.table("contacts").delete().ilike("name", target_name).execute()

        return True
    except Exception as e:
        print(f"Errore eliminazione nodo persona: {e}")
        return False


def update_person_card(node_id: str, data: dict) -> dict | None:
    """Aggiorna la scheda modificabile di una persona (nome, relazione, compleanno, note, foto, parente diretto) su nodes e contacts."""
    if not supabase or not node_id:
        return None
    try:
        node_res = supabase.table("nodes").select("*").eq("id", node_id).execute()
        existing_node = node_res.data[0] if node_res.data else {"id": node_id, "type": "person"}

        name = (data.get("name") or existing_node.get("name") or "").strip()
        relation_type = (data.get("relation_type") or existing_node.get("relation_type") or "neutrale").strip()
        birthday = (data.get("birthday") if "birthday" in data else existing_node.get("birthday") or "").strip()
        notes = (data.get("notes") if "notes" in data else existing_node.get("notes") or "").strip()
        photo_url = (data.get("photo_url") if "photo_url" in data else existing_node.get("photo_url") or "").strip()
        parent_name = (data.get("parent_name") if "parent_name" in data else existing_node.get("parent_name") or "").strip()

        family_keywords = (
            "famiglia", "padre", "madre", "genitore", "figlio", "figlia",
            "fratello", "sorella", "nonno", "nonna", "zio", "zia",
            "cugino", "cugina", "nipote", "marito", "moglie", "coniuge"
        )
        is_family = any(k in relation_type.lower() for k in family_keywords) or existing_node.get("category") == "famiglia" or bool(parent_name)
        category = "famiglia" if is_family else (existing_node.get("category") or "amicizia")

        # Sincronizza la tabella contacts
        old_name = existing_node.get("name") or name
        contact_res = supabase.table("contacts").select("*").ilike("name", old_name).execute()
        contact_payload = {
            "name": name,
            "category": category,
            "relation_type": relation_type,
            "notes": notes,
            "birthday": birthday or None,
            "photo_url": photo_url or None
        }
        if contact_res.data:
            c_id = contact_res.data[0]["id"]
            try:
                supabase.table("contacts").update(contact_payload).eq("id", c_id).execute()
            except Exception:
                contact_payload.pop("birthday", None)
                contact_payload.pop("photo_url", None)
                supabase.table("contacts").update(contact_payload).eq("id", c_id).execute()
        elif node_id != "user_self" and name:
            save_contact_entity(
                name=name,
                category=category,
                notes=notes,
                relation_type=relation_type,
                birthday=birthday or None,
                photo_url=photo_url or None
            )

        # Risolve l'eventuale collegamento diretto impostato manualmente nella scheda
        parent_node_id = None
        if parent_name:
            if parent_name.lower() in ("marco", "marco (tu)", "io"):
                parent_node_id = "user_self"
            else:
                p_match = supabase.table("nodes").select("id").ilike("name", parent_name).execute().data or []
                parent_node_id = p_match[0]["id"] if p_match else make_stable_id("contact", parent_name)

        # Sincronizza il nodo nel grafo 3D
        node_payload = {
            "id": node_id,
            "name": name,
            "type": "core" if node_id == "user_self" else "person",
            "category": "core" if node_id == "user_self" else category,
            "relation_type": relation_type,
            "notes": notes,
            "birthday": birthday or None,
            "photo_url": photo_url or None,
            "parent_name": parent_name or None,
            "parent_node_id": parent_node_id
        }
        try:
            supabase.table("nodes").upsert(node_payload).execute()
        except Exception:
            # Fallback se alcune colonne opzionali non sono ancora state migrate in Supabase
            safe_node = {
                "id": node_id,
                "name": name,
                "type": "core" if node_id == "user_self" else "person",
                "category": "core" if node_id == "user_self" else category,
                "relation_type": relation_type,
                "notes": notes
            }
            supabase.table("nodes").upsert(safe_node).execute()

        # Crea o aggiorna l'arco diretto nel database se è stato indicato un parente/collegamento
        if parent_node_id and parent_node_id != node_id:
            try:
                supabase.table("edges").upsert({
                    "source": parent_node_id,
                    "target": node_id,
                    "relation_type": relation_type or "genitore-figlio",
                    "category": "famiglia" if is_family else "relazione"
                }).execute()
            except Exception:
                pass

        # Salva anche un fatto consolidato se è stato aggiunto un compleanno, così Peter lo ha sempre in memoria
        if birthday and name and node_id != "user_self":
            save_fact(f"Il compleanno di {name} ({relation_type}) è il {birthday}.")

        return node_payload
    except Exception as e:
        print(f"Errore aggiornamento scheda persona: {e}")
        return None


def get_family_and_people_context(limit: int = 50) -> str:
    """Costruisce un riepilogo strutturato di familiari, relazioni dirette, compleanni e note per il contesto LLM di Peter."""
    if not supabase:
        return ""
    try:
        nodes = supabase.table("nodes").select("*").eq("type", "person").limit(limit).execute().data or []
        contacts = supabase.table("contacts").select("*").limit(limit).execute().data or []
        edges = supabase.table("edges").select("*").limit(120).execute().data or []

        id_to_name = {"user_self": "Marco"}
        for n in nodes:
            if n.get("id") and n.get("name"):
                id_to_name[str(n["id"])] = n["name"]

        contact_by_name = {str(c.get("name", "")).strip().lower(): c for c in contacts}
        lines = []
        seen_names = set()

        for n in nodes:
            name = (n.get("name") or "").strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            c_info = contact_by_name.get(name.lower(), {})
            rel = n.get("relation_type") or c_info.get("relation_type") or "contatto"
            bday = n.get("birthday") or c_info.get("birthday") or ""
            notes = n.get("notes") or c_info.get("notes") or ""

            # Ricostruisce i legami diretti dal grafo (padre/madre/figlio/coniuge)
            nid = str(n.get("id"))
            direct_links = []
            for e in edges:
                src, tgt = str(e.get("source", "")), str(e.get("target", ""))
                erel = e.get("relation_type") or ""
                if src == nid and tgt in id_to_name:
                    direct_links.append(f"{erel} -> {id_to_name[tgt]}")
                elif tgt == nid and src in id_to_name:
                    direct_links.append(f"{id_to_name[src]} -> ({erel})")

            parts = [f"- {name} [{rel}]"]
            if bday:
                parts.append(f"Compleanno: {bday}")
            if direct_links:
                parts.append(f"Legami diretti: {', '.join(direct_links)}")
            if notes:
                parts.append(f"Note: {notes}")
            lines.append(" | ".join(parts))

        # Aggiunge eventuali contatti non ancora presenti come nodi
        for c in contacts:
            name = (c.get("name") or "").strip()
            if not name or name.lower() in seen_names:
                continue
            seen_names.add(name.lower())
            rel = c.get("relation_type") or c.get("category") or "contatto"
            bday = c.get("birthday") or ""
            notes = c.get("notes") or ""
            parts = [f"- {name} [{rel}]"]
            if bday:
                parts.append(f"Compleanno: {bday}")
            if notes:
                parts.append(f"Note: {notes}")
            lines.append(" | ".join(parts))

        return "\n".join(lines)
    except Exception as e:
        print(f"Errore lettura contesto persone/famiglia: {e}")
        return ""


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
