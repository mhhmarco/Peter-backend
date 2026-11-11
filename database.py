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

# === MEMORIA EPISODICA & SEMANTICA ===
def get_recent_memories(limit: int = 8) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("memories").select("content").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([item["content"] for item in reversed(res.data)])
    except Exception as e:
        print(f"Errore lettura memories: {e}")
    return ""

def save_episodic_memory(user_msg: str, peter_reply: str):
    if not supabase:
        return
    try:
        supabase.table("memories").insert([
            {"content": f"Marco: {user_msg}"},
            {"content": f"Peter: {peter_reply}"}
        ]).execute()
    except Exception as e:
        print(f"Errore salvataggio memoria episodica: {e}")

def get_long_term_facts(limit: int = 15) -> str:
    if not supabase:
        return ""
    try:
        res = supabase.table("user_facts").select("fact").order("created_at", desc=True).limit(limit).execute()
        if res.data:
            return "\n".join([f"- {item['fact']}" for item in res.data])
    except Exception as e:
        print(f"Errore lettura facts: {e}")
    return ""

def get_all_facts():
    if not supabase:
        return []
    try:
        res = supabase.table("user_facts").select("*").order("created_at", desc=True).execute()
        return res.data or []
    except Exception as e:
        return []

def delete_fact_by_id(fact_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("user_facts").delete().eq("id", fact_id).execute()
        return True
    except Exception as e:
        return False

def save_fact_deduplicated(fact_text: str):
    if not supabase or not fact_text:
        return
    clean_fact = fact_text.strip()
    try:
        existing = supabase.table("user_facts").select("fact").ilike("fact", f"%{clean_fact[:15]}%").execute()
        if existing.data and len(existing.data) > 0:
            return
        supabase.table("user_facts").insert([{"fact": clean_fact}]).execute()
    except Exception as e:
        print(f"Errore salvataggio fatto: {e}")

# === NEXUS CONTACTS VAULT & SCHEDE CONTATTO ===
def get_graph_data():
    if not supabase:
        return {"nodes": [], "edges": []}
    try:
        nodes = supabase.table("nodes").select("*").order("created_at", desc=True).execute().data or []
        edges = supabase.table("edges").select("*").order("created_at", desc=True).execute().data or []
        return {"nodes": nodes, "edges": edges}
    except Exception as e:
        print(f"Errore recupero dati grafo: {e}")
        return {"nodes": [], "edges": []}

def add_or_update_node(name: str, category: str = "Amicizia", notes: str = "", role: str = "", phone: str = "", email: str = "") -> dict:
    if not supabase or not name:
        return None
    try:
        clean_name = name.strip()
        existing = supabase.table("nodes").select("*").ilike("name", clean_name).execute()
        payload = {
            "name": clean_name,
            "category": category,
            "notes": notes,
            "role": role,
            "phone": phone,
            "email": email
        }
        if existing.data:
            node_id = existing.data[0]["id"]
            res = supabase.table("nodes").update(payload).eq("id", node_id).execute()
            return res.data[0] if res.data else existing.data[0]
        else:
            res = supabase.table("nodes").insert([payload]).execute()
            return res.data[0] if res.data else None
    except Exception as e:
        print(f"Errore salvataggio scheda contatto: {e}")
        return None

def sync_bulk_contacts(contacts_list: list) -> int:
    """Importa in blocco una lista di contatti nella rubrica Nexus."""
    if not supabase or not contacts_list:
        return 0
    count = 0
    for c in contacts_list:
        name = c.get("name")
        if name:
            add_or_update_node(
                name=name,
                category=c.get("category", "Amicizia"),
                notes=c.get("notes", ""),
                role=c.get("role", ""),
                phone=c.get("phone", ""),
                email=c.get("email", "")
            )
            count += 1
    return count

def add_edge(source_id: str, target_id: str, relation_label: str = "collegato") -> dict:
    if not supabase or not source_id or not target_id:
        return None
    try:
        existing = supabase.table("edges").select("*")\
            .eq("source_id", source_id)\
            .eq("target_id", target_id)\
            .eq("relation_label", relation_label).execute()
        if existing.data:
            return existing.data[0]

        res = supabase.table("edges").insert([{
            "source_id": source_id,
            "target_id": target_id,
            "relation_label": relation_label
        }]).execute()
        return res.data[0] if res.data else None
    except Exception as e:
        print(f"Errore salvataggio relazione: {e}")
        return None

def delete_node_by_id(node_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("edges").delete().or_(f"source_id.eq.{node_id},target_id.eq.{node_id}").execute()
        supabase.table("nodes").delete().eq("id", node_id).execute()
        return True
    except Exception as e:
        print(f"Errore eliminazione nodo: {e}")
        return False

def delete_edge_by_id(edge_id: str) -> bool:
    if not supabase:
        return False
    try:
        supabase.table("edges").delete().eq("id", edge_id).execute()
        return True
    except Exception as e:
        return False
