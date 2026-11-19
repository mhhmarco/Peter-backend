_from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter

from database import supabase

router = APIRouter()

_FAMILY_TERMS = (
    "famiglia", "family", "padre", "madre", "genitor", "figli", "fratell",
    "sorell", "nonn", "zi", "cugin", "nipot", "marito", "moglie", "coniug",
    "suocer", "cognat", "parent", "prozi",
)

# Relazioni genealogiche dirette consentite nell'albero familiare (genitore-figlio e coniugi)
_DIRECT_TREE_RELATIONS = (
    "padre", "madre", "genitore", "figlio", "figlia", "marito", "moglie", "coniuge", "genitore-figlio"
)

_INVALID_NAMES = {"nessuno", "utente", "sconosciuto", "anonimo", "marco", "marco (tu)", "io"}


def _family(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(term in text for term in _FAMILY_TERMS)


def _is_direct_genealogy_edge(relation: Any) -> bool:
    text = str(relation or "").casefold()
    return any(term in text for term in _DIRECT_TREE_RELATIONS)


def _norm_name(name: Any) -> str:
    return re.sub(r"\s+", " ", str(name or "").strip()).casefold()


def _rows(table: str, columns: str = "*") -> list[dict]:
    if not supabase:
        return []
    try:
        # Supabase/PostgREST caps a response page; walk pages to include the full history.
        output: list[dict] = []
        start = 0
        page_size = 1000
        while True:
            page = (supabase.table(table).select(columns).range(start, start + page_size - 1).execute().data or [])
            output.extend(dict(item) for item in page)
            if len(page) < page_size:
                break
            start += page_size
        return output
    except Exception as exc:
        print(f"Errore lettura grafo {table}: {exc}")
        return []


def _enrich_and_deduplicate_people(raw_nodes: list[dict], raw_edges: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Deduplica i nodi persona con lo stesso nome (eliminando le 'persone in più' create da estrattori multipli),
    rimuove nomi non validi e rimappa tutti gli archi sugli ID canonici.
    """
    contacts = _rows("contacts")
    contacts_by_name = {_norm_name(c.get("name")): c for c in contacts if c.get("name")}

    canonical_by_name: dict[str, dict] = {}
    id_remap: dict[str, str] = {"user_self": "user_self"}

    for node in raw_nodes:
        nid = str(node.get("id", "")).strip()
        if not nid or nid == "user_self" or node.get("type") != "person":
            continue
        name = str(node.get("name") or "").strip()
        norm = _norm_name(name)
        # Scarta voci vuote, segnaposto o frasi erroneamente estratte come nomi
        if not norm or norm in _INVALID_NAMES or len(name) > 45:
            continue

        c = contacts_by_name.get(norm, {})
        if norm not in canonical_by_name:
            merged = dict(node)
            merged["id"] = nid
            merged["name"] = name
            if not merged.get("birthday") and c.get("birthday"):
                merged["birthday"] = c.get("birthday")
            if not merged.get("photo_url") and c.get("photo_url"):
                merged["photo_url"] = c.get("photo_url")
            if not merged.get("notes") and c.get("notes"):
                merged["notes"] = c.get("notes")
            if not merged.get("birth_year") and c.get("birth_year"):
                merged["birth_year"] = c.get("birth_year")
            if (not merged.get("relation_type") or merged.get("relation_type") == "neutrale") and c.get("relation_type"):
                merged["relation_type"] = c.get("relation_type")
            canonical_by_name[norm] = merged
        else:
            # Unisce le informazioni del duplicato nel nodo canonico
            existing = canonical_by_name[norm]
            for field in ("birthday", "photo_url", "birth_year", "parent_node_id", "parent_id", "parent_name"):
                if not existing.get(field) and node.get(field):
                    existing[field] = node.get(field)
            if node.get("notes") and node["notes"] not in (existing.get("notes") or ""):
                existing["notes"] = f"{existing.get('notes', '')} | {node['notes']}".strip(" |")
            if (not existing.get("relation_type") or existing.get("relation_type") == "neutrale") and node.get("relation_type"):
                existing["relation_type"] = node.get("relation_type")

        id_remap[nid] = canonical_by_name[norm]["id"]

    remapped_edges: list[dict] = []
    seen_pairs: set[tuple[str, str, str]] = set()
    for edge in raw_edges:
        src = id_remap.get(str(edge.get("source", "")).strip(), str(edge.get("source", "")).strip())
        tgt = id_remap.get(str(edge.get("target", "")).strip(), str(edge.get("target", "")).strip())
        rel = str(edge.get("relation_type") or "").strip()
        if not src or not tgt or src == tgt:
            continue
        key = (src, tgt, rel.casefold())
        if key not in seen_pairs:
            seen_pairs.add(key)
            remapped_edges.append({**edge, "source": src, "target": tgt})

    return list(canonical_by_name.values()), remapped_edges


def _auto_wire_family_tree(family_nodes: list[dict], edges: list[dict]) -> list[dict]:
    """
    Ricostruisce automaticamente i rami dell'albero genealogico fino a Marco ('user_self')
    usando legami diretti (genitore -> figlio, marito <-> moglie) e colmando eventuali
    salti generazionali (es. 'nonna materna' -> 'madre' -> 'Marco').
    """
    node_ids = {n["id"] for n in family_nodes}
    by_name = {_norm_name(n.get("name")): n["id"] for n in family_nodes}
    by_name["marco"] = "user_self"
    by_name["marco (tu)"] = "user_self"

    # Individua i nodi chiave di primo grado di Marco (padre, madre) se presenti nel grafo
    marco_mother_id = None
    marco_father_id = None
    for n in family_nodes:
        if n["id"] == "user_self":
            continue
        rel = _norm_name(n.get("relation_type"))
        notes = _norm_name(n.get("notes"))
        if ("madre" in rel or "mamma" in rel) and "nonn" not in rel and "suocer" not in rel:
            marco_mother_id = n["id"]
        elif ("padre" in rel or "papà" in rel or "papa" in rel) and "nonn" not in rel and "suocer" not in rel:
            marco_father_id = n["id"]
        elif "madre di marco" in notes:
            marco_mother_id = n["id"]
        elif "padre di marco" in notes:
            marco_father_id = n["id"]

    tree_edges: list[dict] = []
    pair_set: set[tuple[str, str]] = set()

    def add_tree_edge(src: str, tgt: str, label: str):
        if not src or not tgt or src == tgt:
            return
        if src not in node_ids or tgt not in node_ids:
            return
        # Evita doppi archi opposti che creerebbero cicli nel layout gerarchico DAG
        if (src, tgt) in pair_set or (tgt, src) in pair_set:
            return
        pair_set.add((src, tgt))
        tree_edges.append({
            "source": src,
            "target": tgt,
            "relation_type": label,
            "category": "famiglia",
            "family_tree": True
        })

    # 1. Mantieni gli archi genealogici diretti già salvati nel DB (escludendo raggi diretti errati verso Marco di nonni/zii)
    for edge in edges:
        src, tgt = edge["source"], edge["target"]
        rel = str(edge.get("relation_type") or "")
        if src not in node_ids or tgt not in node_ids:
            continue
        if not _is_direct_genealogy_edge(rel):
            continue
        if src == "user_self" or tgt == "user_self":
            other_id = tgt if src == "user_self" else src
            other_node = next((n for n in family_nodes if n["id"] == other_id), {})
            other_rel = _norm_name(other_node.get("relation_type"))
            # Solo genitori, figli o coniuge di Marco possono avere un arco diretto con user_self
            if any(k in other_rel for k in ("nonn", "zi", "cugin", "prozi", "suocer", "cognat", "nipot")):
                continue
        add_tree_edge(src, tgt, rel or "famiglia")

    # 2. Onora parent_node_id / parent_id / parent_name espliciti
    for n in family_nodes:
        if n["id"] == "user_self":
            continue
        parent = n.get("parent_node_id") or n.get("parent_id")
        if not parent and n.get("parent_name"):
            parent = by_name.get(_norm_name(n["parent_name"]))
        if parent:
            add_tree_edge(str(parent), n["id"], n.get("family_relation") or "genitore-figlio")

    # 3. Ricostruisci i collegamenti genealogici mancanti per i nodi ancora scollegati (es. Nadia Rizzuti · nonna materna)
    connected_ids = set()
    for s, t in pair_set:
        connected_ids.add(s)
        connected_ids.add(t)

    for n in family_nodes:
        nid = n["id"]
        if nid == "user_self" or nid in connected_ids:
            continue
        rel = _norm_name(n.get("relation_type"))
        notes = _norm_name(n.get("notes"))

        # Cerca eventuale riferimento esplicito nelle note ("madre di <Nome>", "padre di <Nome>", "figlio di <Nome>")
        matched_via_notes = False
        for other_name_norm, other_id in by_name.items():
            if other_id == nid or len(other_name_norm) < 3:
                continue
            if f"madre di {other_name_norm}" in notes or f"padre di {other_name_norm}" in notes or f"genitore di {other_name_norm}" in notes:
                add_tree_edge(nid, other_id, rel or "genitore")
                matched_via_notes = True
                break
            if f"figlio di {other_name_norm}" in notes or f"figlia di {other_name_norm}" in notes:
                add_tree_edge(other_id, nid, rel or "figlio/a")
                matched_via_notes = True
                break
            if f"moglie di {other_name_norm}" in notes or f"marito di {other_name_norm}" in notes:
                add_tree_edge(nid, other_id, rel or "coniuge")
                matched_via_notes = True
                break

        if matched_via_notes:
            continue

        # Catena genealogica standard per nonni, genitori, fratelli, zii
        if "nonn" in rel and "matern" in rel:
            target = marco_mother_id or "user_self"
            add_tree_edge(nid, target, rel)
        elif "nonn" in rel and "patern" in rel:
            target = marco_father_id or "user_self"
            add_tree_edge(nid, target, rel)
        elif "nonn" in rel:
            target = marco_mother_id or marco_father_id or "user_self"
            add_tree_edge(nid, target, rel)
        elif ("madre" in rel or "mamma" in rel or "padre" in rel or "papà" in rel) and "suocer" not in rel:
            add_tree_edge(nid, "user_self", rel)
        elif "fratell" in rel or "sorell" in rel:
            parent_anchor = marco_mother_id or marco_father_id or "user_self"
            add_tree_edge(parent_anchor, nid, rel)
        elif "zi" in rel and "matern" in rel and marco_mother_id:
            # Collega lo zio materno alla nonna materna se presente, altrimenti alla madre
            maternal_grandparent = next((s for s, t in pair_set if t == marco_mother_id), None)
            add_tree_edge(maternal_grandparent or marco_mother_id, nid, rel)
        elif "zi" in rel and "patern" in rel and marco_father_id:
            paternal_grandparent = next((s for s, t in pair_set if t == marco_father_id), None)
            add_tree_edge(paternal_grandparent or marco_father_id, nid, rel)
        elif any(k in rel for k in ("figli", "marito", "moglie", "coniug")):
            add_tree_edge("user_self", nid, rel)

    return tree_edges


def _people_graph(family_only: bool) -> dict:
    raw_nodes = _rows("nodes")
    raw_edges = _rows("edges")
    dedup_nodes, remapped_edges = _enrich_and_deduplicate_people(raw_nodes, raw_edges)

    normalized: list[dict] = []
    node_ids: set[str] = set()

    for node in dedup_nodes:
        is_family = _family(f"{node.get('category', '')} {node.get('relation_type', '')} {node.get('relationship_group', '')}")
        if is_family != family_only:
            continue
        node["relationship_group"] = "family" if is_family else "friend"
        normalized.append(node)
        node_ids.add(node["id"])

    # Nodo centrale fisso all'origine (0, 0, 0) per mantenere il grafo sempre perfettamente centrato
    core = {
        "id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core",
        "notes": "Admin & Core Neural Center", "gender": "M", "birth_year": 2006,
        "fx": 0, "fy": 0, "fz": 0,
    }
    normalized.append(core)
    node_ids.add("user_self")

    if family_only:
        tree_edges = _auto_wire_family_tree(normalized, remapped_edges)
        return {"nodes": normalized, "edges": tree_edges}

    filtered_edges: list[dict] = []
    seen = set()
    for edge in remapped_edges:
        source, target = edge["source"], edge["target"]
        if source not in node_ids or target not in node_ids or (source, target) in seen:
            continue
        seen.add((source, target))
        filtered_edges.append({
            **edge,
            "source": source,
            "target": target,
            "category": "relazione"
        })

    # Collega a Marco eventuali contatti non familiari ancora isolati nella vista relazioni
    connected = {e["source"] for e in filtered_edges} | {e["target"] for e in filtered_edges}
    for node in normalized:
        if node["id"] != "user_self" and node["id"] not in connected:
            filtered_edges.append({
                "source": "user_self",
                "target": node["id"],
                "relation_type": node.get("relation_type") or "contatto",
                "category": "relazione"
            })

    return {"nodes": normalized, "edges": filtered_edges}


def _memory_graph(table: str, column: str, kind: str) -> dict:
    records = _rows(table, f"id,{column},created_at")
    nodes = []
    for index, record in enumerate(records):
        record_id = record.get("id")
        if record_id is None:
            record_id = f"{kind}_{index}"
        text = str(record.get(column) or "").strip()
        if not text:
            continue
        nodes.append({
            "id": f"{kind}_{record_id}", "type": kind,
            "name": text[:90], "notes": text,
            "created_at": record.get("created_at"), "category": kind,
        })
    edges = []
    for node in nodes:
        edges.append({"source": "user_self", "target": node["id"], "relation_type": "ricordo a lungo termine", "category": "memory"})
    # Inserisce sempre Marco al centro (0, 0, 0) anche quando non ci sono ancora fatti salvati
    nodes.insert(0, {
        "id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core",
        "notes": "Admin & Core Neural Center", "fx": 0, "fy": 0, "fz": 0
    })
    return {"nodes": nodes, "edges": edges}


@router.get("/api/nexus/{graph_type}")
def get_nexus_view(graph_type: str):
    if graph_type == "family":
        return _people_graph(family_only=True)
    if graph_type == "people":
        return _people_graph(family_only=False)
    if graph_type == "facts":
        return _memory_graph("user_facts", "fact", "memory")
    # La vista "chats" è stata rimossa dal grafo 3D su richiesta dell'utente
    return {"nodes": [], "edges": [], "error": "Vista grafo non riconosciuta"}
