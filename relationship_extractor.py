import hashlib
import json
import re

import httpx

from config import GROQ_API_KEY, GROQ_URL
from database import supabase


_CORE_ALIASES = {"marco", "barbi", "marco barbiero", "marco barbiero torres", "io", "me"}
_FAMILY = re.compile(r"famigli|family|padre|madre|genitor|figli|fratell|sorell|nonn|zi[oa]|cugin|nipot|marito|moglie|suocer|cognat", re.I)


def _json_from_response(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end < start:
        return {}
    try:
        value = json.loads(raw[start:end + 1])
        return value if isinstance(value, dict) else {}
    except json.JSONDecodeError:
        return {}


def _get_or_create_person(person: dict) -> str | None:
    name = str(person.get("name") or "").strip()
    if not name or name.casefold() in _CORE_ALIASES or not supabase:
        return "user_self" if name.casefold() in _CORE_ALIASES else None
    try:
        found = supabase.table("nodes").select("id").ilike("name", name).limit(1).execute().data or []
        relation = str(person.get("relation_type") or "conoscente").strip()
        family = bool(_FAMILY.search(relation))
        node_id = str(found[0]["id"]) if found else "person_" + hashlib.sha256(name.casefold().encode("utf-8")).hexdigest()[:20]
        node_data = {
            "id": node_id, "name": name, "type": "person",
            "category": "famiglia" if family else "amicizia",
            "relationship_group": "family" if family else "friend",
            "relation_type": relation,
        }
        if person.get("gender"):
            node_data["gender"] = person["gender"]
        if person.get("birth_year"):
            node_data["birth_year"] = person["birth_year"]
        # Save parent metadata only when the message explicitly named a parent.
        if person.get("parent_name"):
            parent_name = str(person["parent_name"]).strip()
            parent = supabase.table("nodes").select("id").ilike("name", parent_name).limit(1).execute().data or []
            if parent:
                node_data["parent_node_id"] = str(parent[0]["id"])
                node_data["family_relation"] = str(person.get("family_relation") or "genitore-figlio")
        supabase.table("nodes").upsert(node_data).execute()
        return node_id
    except Exception as exc:
        print(f"Errore aggiornamento relazione persona {name}: {exc}")
        return None


async def extract_and_save_relationships(message: str) -> None:
    """Persist only relationships the user stated explicitly; never infer kinship."""
    if not GROQ_API_KEY or not supabase or not message.strip():
        return
    prompt = (
        "Estrai esclusivamente persone e relazioni esplicitamente dichiarate nel messaggio. "
        "Non dedurre parentele, amicizie o collegamenti. Se una persona è collegata solo a Marco, "
        "related_to deve essere Marco. related_to può indicare un'altra persona solo quando il testo "
        "spiega chiaramente il loro rapporto. parent_name va valorizzato solo per un legame genitore-figlio "
        "esplicito. Restituisci SOLO JSON: {\"people\":[{\"name\":\"...\",\"relation_type\":\"...\",\"related_to\":\"...\",\"parent_name\":\"...\",\"family_relation\":\"...\",\"gender\":\"...\",\"birth_year\":null}]}\n"
        "Se non ci sono dati espliciti, restituisci {\"people\":[]}. Messaggio:\n" + message[:6000]
    )
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                GROQ_URL,
                json={"model": "allam-2-7b", "messages": [{"role": "user", "content": prompt}], "temperature": 0},
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {GROQ_API_KEY}"},
            )
        if response.status_code != 200:
            return
        raw = response.json().get("choices", [{}])[0].get("message", {}).get("content", "")
        people = _json_from_response(raw).get("people", [])
        if not isinstance(people, list):
            return
        resolved = {}
        for person in people:
            if isinstance(person, dict) and person.get("name"):
                node_id = _get_or_create_person(person)
                if node_id:
                    resolved[str(person["name"]).strip().casefold()] = node_id
        for person in people:
            if not isinstance(person, dict) or not person.get("name"):
                continue
            source = resolved.get(str(person["name"]).strip().casefold())
            target_name = str(person.get("related_to") or "").strip()
            target = "user_self" if target_name.casefold() in _CORE_ALIASES else resolved.get(target_name.casefold())
            if not source or not target or source == target:
                continue
            relation = str(person.get("relation_type") or "relazione esplicita").strip()
            edge = {"source": target, "target": source, "relation_type": relation,
                    "category": "famiglia" if _FAMILY.search(relation) else "relazione"}
            if person.get("parent_name"):
                parent_name = str(person["parent_name"]).strip()
                parent_id = "user_self" if parent_name.casefold() in _CORE_ALIASES else resolved.get(parent_name.casefold())
                if parent_id:
                    edge["source"], edge["target"] = parent_id, source
                    edge["category"] = "famiglia"
                    edge["family_tree"] = True
                    supabase.table("nodes").update({"parent_node_id": parent_id, "family_relation": str(person.get("family_relation") or relation)}).eq("id", source).execute()
            supabase.table("edges").upsert(edge).execute()
    except Exception as exc:
        print(f"Errore estrazione relazioni: {exc}")
