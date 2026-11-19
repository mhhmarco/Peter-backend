from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from database import supabase

router = APIRouter()

_FAMILY_TERMS = (
    "famiglia", "family", "padre", "madre", "genitor", "figli", "fratell",
    "sorell", "nonn", "zi", "cugin", "nipot", "marito", "moglie", "coniug",
    "suocer", "cognat", "parent",
)

# Relazioni genealogiche dirette consentite nell'albero familiare (genitore-figlio e coniugi)
_DIRECT_TREE_RELATIONS = (
    "padre", "madre", "genitore", "figlio", "figlia", "marito", "moglie", "coniuge", "genitore-figlio"
)


def _family(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(term in text for term in _FAMILY_TERMS)


def _is_direct_genealogy_edge(relation: Any) -> bool:
    text = str(relation or "").casefold()
    return any(term in text for term in _DIRECT_TREE_RELATIONS)


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


def _enrich_nodes_with_contacts(nodes: list[dict]) -> list[dict]:
    """Unisce compleanno, foto e note dalla tabella contacts ai nodi del grafo per l'ispettore 3D."""
    contacts = _rows("contacts")
    by_name = {str(c.get("name", "")).strip().casefold(): c for c in contacts if c.get("name")}
    for node in nodes:
        if node.get("type") != "person":
            continue
        c = by_name.get(str(node.get("name", "")).strip().casefold())
        if c:
            if not node.get("birthday") and c.get("birthday"):
                node["birthday"] = c.get("birthday")
            if not node.get("photo_url") and c.get("photo_url"):
                node["photo_url"] = c.get("photo_url")
            if not node.get("notes") and c.get("notes"):
                node["notes"] = c.get("notes")
            if not node.get("birth_year") and c.get("birth_year"):
                node["birth_year"] = c.get("birth_year")
    return nodes


def _people_graph(family_only: bool) -> dict:
    nodes = _enrich_nodes_with_contacts(_rows("nodes"))
    edges = _rows("edges")
    normalized: list[dict] = []
    node_ids: set[str] = set()

    for node in nodes:
        if node.get("type") != "person":
            continue
        is_family = _family(f"{node.get('category', '')} {node.get('relation_type', '')} {node.get('relationship_group', '')}")
        if is_family != family_only:
            continue
        node["id"] = str(node.get("id", ""))
        if not node["id"]:
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

    # Raccoglie tutti gli archi genealogici diretti tra familiari (padre/madre -> figlio/a, marito <-> moglie)
    direct_family_nodes: set[str] = set()
    if family_only:
        for edge in edges:
            src, tgt = str(edge.get("source", "")), str(edge.get("target", ""))
            rel = str(edge.get("relation_type", ""))
            if src in node_ids and tgt in node_ids and _is_direct_genealogy_edge(rel):
                if src != "user_self" and tgt != "user_self":
                    direct_family_nodes.add(src)
                    direct_family_nodes.add(tgt)

    filtered_edges: list[dict] = []
    for edge in edges:
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        if source not in node_ids or target not in node_ids:
            continue
        relation = str(edge.get("relation_type", ""))
        edge_is_family = _family(f"{relation} {edge.get('category', '')}")
        if edge_is_family != family_only:
            continue

        if family_only:
            # Nell'albero familiare consentiamo SOLO legami diretti (padre, madre, figlio, figlia, marito, moglie)
            if not _is_direct_genealogy_edge(relation):
                continue
            # Evita raggi ridondanti verso Marco se la persona ha già un collegamento genealogico diretto con un genitore/coniuge
            other = target if source == "user_self" else source if target == "user_self" else None
            if other:
                other_node = next((node for node in normalized if node["id"] == other), {})
                rel_lower = relation.casefold()
                is_marco_direct_parent_or_spouse = any(
                    k in rel_lower for k in ("padre", "madre", "figlio", "figlia", "marito", "moglie", "coniuge")
                ) and not any(k in rel_lower for k in ("nonn", "zi", "cugin", "prozi", "suocer", "cognat"))
                if not is_marco_direct_parent_or_spouse or (
                    other in direct_family_nodes and (other_node.get("parent_node_id") or other_node.get("parent_id") or other_node.get("parent_name"))
                ):
                    continue

        filtered_edges.append({
            **edge,
            "source": source,
            "target": target,
            "category": "famiglia" if edge_is_family else "relazione"
        })

    # Honor explicit parent fields even when a corresponding edge hasn't been saved yet.
    existing = {(edge["source"], edge["target"]) for edge in filtered_edges}
    if family_only:
        by_name = {str(node.get("name", "")).strip().casefold(): node["id"] for node in normalized}
        by_name["marco"] = "user_self"
        by_name["marco (tu)"] = "user_self"
        for node in normalized:
            if node.get("type") != "person":
                continue
            parent = node.get("parent_node_id") or node.get("parent_id")
            if not parent and node.get("parent_name"):
                parent = by_name.get(str(node["parent_name"]).strip().casefold())
            if parent:
                parent = str(parent)
                if parent in node_ids and parent != node["id"] and (parent, node["id"]) not in existing:
                    filtered_edges.append({
                        "source": parent,
                        "target": node["id"],
                        "relation_type": node.get("family_relation") or "genitore-figlio",
                        "category": "famiglia",
                        "family_tree": True
                    })
                    existing.add((parent, node["id"]))
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
