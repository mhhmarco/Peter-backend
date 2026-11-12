from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from database import supabase

router = APIRouter()

_FAMILY_TERMS = (
    "famiglia", "family", "padre", "madre", "genitor", "figli", "fratell",
    "sorell", "nonn", "zi", "cugin", "nipot", "marito", "moglie",
    "suocer", "cognat", "parent",
)


def _family(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(term in text for term in _FAMILY_TERMS)


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


def _people_graph(family_only: bool) -> dict:
    nodes = _rows("nodes")
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

    core = {
        "id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core",
        "notes": "Admin & Core Neural Center", "gender": "M", "birth_year": 2006,
    }
    normalized.append(core)
    node_ids.add("user_self")
    filtered_edges: list[dict] = []
    for edge in edges:
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        if source not in node_ids or target not in node_ids:
            continue
        relation = str(edge.get("relation_type", ""))
        edge_is_family = _family(f"{relation} {edge.get('category', '')}")
        if edge_is_family != family_only:
            continue
        # When a parent's explicit genealogy edge exists, don't also draw a misleading
        # direct-to-Marco spoke for that same family member.
        child = target if source == "user_self" else source if target == "user_self" else None
        if family_only and child:
            child_node = next((node for node in normalized if node["id"] == child), {})
            if child_node.get("parent_node_id") or child_node.get("parent_id") or child_node.get("parent_name"):
                continue
        filtered_edges.append({**edge, "source": source, "target": target, "category": "famiglia" if edge_is_family else "relazione"})

    # Honor explicit parent fields even when a corresponding edge hasn't been saved yet.
    existing = {(edge["source"], edge["target"]) for edge in filtered_edges}
    if family_only:
        by_name = {str(node.get("name", "")).strip().casefold(): node["id"] for node in normalized}
        for node in normalized:
            if node.get("type") != "person":
                continue
            parent = node.get("parent_node_id") or node.get("parent_id")
            if not parent and node.get("parent_name"):
                parent = by_name.get(str(node["parent_name"]).strip().casefold())
            if parent:
                parent = str(parent)
                if parent in node_ids and parent != node["id"] and (parent, node["id"]) not in existing:
                    filtered_edges.append({"source": parent, "target": node["id"], "relation_type": node.get("family_relation") or "genitore-figlio", "category": "famiglia", "family_tree": True})
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
    if kind == "chat":
        # Conversation records form a chronological thread instead of a star around Marco.
        for previous, current in zip(nodes, nodes[1:]):
            edges.append({"source": previous["id"], "target": current["id"], "relation_type": "chat successiva", "category": "conversation"})
    else:
        for node in nodes:
            edges.append({"source": "user_self", "target": node["id"], "relation_type": "ricordo a lungo termine", "category": "memory"})
        if nodes:
            nodes.insert(0, {"id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core"})
    return {"nodes": nodes, "edges": edges}


@router.get("/api/nexus/{graph_type}")
def get_nexus_view(graph_type: str):
    if graph_type == "family":
        return _people_graph(family_only=True)
    if graph_type == "people":
        return _people_graph(family_only=False)
    if graph_type == "chats":
        return _memory_graph("memories", "content", "chat")
    if graph_type == "facts":
        return _memory_graph("user_facts", "fact", "memory")
    return {"nodes": [], "edges": [], "error": "Vista grafo non riconosciuta"}
