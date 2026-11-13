from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database import supabase

router = APIRouter()

_FAMILY_TERMS = (
    "famiglia", "family", "padre", "madre", "genitor", "figli", "fratell",
    "sorell", "nonn", "zi", "cugin", "nipot", "marito", "moglie",
    "suocer", "cognat", "parent",
)


class PersonUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    gender: str | None = None
    birth_year: int | None = None
    relation_type: str | None = None
    relationship_group: str | None = None
    category: str | None = None
    notes: str | None = None
    parent_node_id: str | None = None
    family_relation: str | None = None


class FactUpdate(BaseModel):
    fact: str = Field(min_length=1, max_length=10000)
    topics: list[str] = Field(default_factory=list, max_length=30)


def _family(value: Any) -> bool:
    text = str(value or "").casefold()
    return any(term in text for term in _FAMILY_TERMS)


def _rows(table: str, columns: str = "*") -> list[dict]:
    if not supabase:
        return []
    try:
        output: list[dict] = []
        start = 0
        page_size = 1000
        while True:
            page = (supabase.table(table).select(columns)
                    .range(start, start + page_size - 1).execute().data or [])
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

    core = {"id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core",
            "notes": "Admin & Core Neural Center", "gender": "M", "birth_year": 2006}
    normalized.append(core)
    node_ids.add("user_self")
    filtered_edges: list[dict] = []
    for edge in edges:
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        if source not in node_ids or target not in node_ids:
            continue
        edge_is_family = _family(f"{edge.get('relation_type', '')} {edge.get('category', '')}")
        if edge_is_family != family_only:
            continue
        child = target if source == "user_self" else source if target == "user_self" else None
        child_node = next((node for node in normalized if node["id"] == child), {})
        if family_only and child and (child_node.get("parent_node_id") or child_node.get("parent_id") or child_node.get("parent_name")):
            continue
        filtered_edges.append({**edge, "source": source, "target": target,
                               "category": "famiglia" if edge_is_family else "relazione"})

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
                    filtered_edges.append({"source": parent, "target": node["id"],
                                           "relation_type": node.get("family_relation") or "genitore-figlio",
                                           "category": "famiglia", "family_tree": True})
    return {"nodes": normalized, "edges": filtered_edges}


def _memory_graph(table: str, column: str, kind: str) -> dict:
    columns = f"id,{column},created_at" + (",topics" if kind == "memory" else "")
    records = _rows(table, columns)
    nodes = []
    for index, record in enumerate(records):
        record_id = record.get("id", f"{kind}_{index}")
        text = str(record.get(column) or "").strip()
        if not text:
            continue
        nodes.append({"id": f"{kind}_{record_id}", "type": kind, "name": text[:90],
                      "notes": text, "created_at": record.get("created_at"), "category": kind,
                      "topics": record.get("topics") or []})
    edges = []
    if kind == "chat":
        for previous, current in zip(nodes, nodes[1:]):
            edges.append({"source": previous["id"], "target": current["id"],
                          "relation_type": "chat successiva", "category": "conversation"})
    else:
        topic_nodes: dict[str, list[str]] = {}
        for node in nodes:
            for topic in node["topics"]:
                normalized_topic = str(topic).strip().casefold()
                if normalized_topic:
                    topic_nodes.setdefault(normalized_topic, []).append(node["id"])
        pairs = set()
        for topic, ids in topic_nodes.items():
            for index, source in enumerate(ids):
                for target in ids[index + 1:]:
                    pair = tuple(sorted((source, target)))
                    if pair not in pairs:
                        edges.append({"source": pair[0], "target": pair[1],
                                      "relation_type": f"argomento: {topic}", "category": "shared-topic"})
                        pairs.add(pair)
        if nodes:
            nodes.insert(0, {"id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core"})
            edges.extend({"source": "user_self", "target": node["id"],
                          "relation_type": "ricordo a lungo termine", "category": "memory"} for node in nodes[1:])
    return {"nodes": nodes, "edges": edges}


def _unified_graph() -> dict:
    nodes = _rows("nodes")
    edges = _rows("edges")
    present = {str(node.get("id")) for node in nodes}
    if "user_self" not in present:
        nodes.append({"id": "user_self", "name": "Marco (Tu)", "type": "core", "category": "core", "gender": "M"})
        present.add("user_self")
    for table, field, kind in (("memories", "content", "chat"), ("user_facts", "fact", "memory"),
                               ("calendar_events", "title", "event"), ("interests", "name", "interest")):
        cols = f"id,{field},created_at" + (",topics" if kind == "memory" else "")
        for row in _rows(table, cols):
            if not row.get(field):
                continue
            node_id = f"{kind}_{row.get('id')}"
            if node_id in present:
                continue
            nodes.append({"id": node_id, "name": str(row[field])[:100], "notes": str(row[field]),
                          "type": kind, "category": kind, "topics": row.get("topics") or [],
                          "created_at": row.get("created_at")})
            present.add(node_id)
            if kind == "memory":
                edges.append({"source": "user_self", "target": node_id, "relation_type": "ricordo a lungo termine", "category": "memory"})
    topics: dict[str, list[str]] = {}
    for node in nodes:
        for topic in node.get("topics") or []:
            key = str(topic).strip().casefold()
            if key:
                topics.setdefault(key, []).append(str(node.get("id")))
    existing_pairs = set()
    for topic, ids in topics.items():
        for i, source in enumerate(ids):
            for target in ids[i + 1:]:
                pair = tuple(sorted((source, target)))
                if pair not in existing_pairs:
                    edges.append({"source": pair[0], "target": pair[1], "relation_type": f"argomento: {topic}", "category": "shared-topic"})
                    existing_pairs.add(pair)
    return {"nodes": nodes, "edges": edges}


@router.get("/api/nexus/{graph_type}")
def get_nexus_view(graph_type: str):
    if graph_type == "all":
        return _unified_graph()
    if graph_type == "family":
        return _people_graph(family_only=True)
    if graph_type == "people":
        return _people_graph(family_only=False)
    if graph_type == "chats":
        return _memory_graph("memories", "content", "chat")
    if graph_type == "facts":
        return _memory_graph("user_facts", "fact", "memory")
    return {"nodes": [], "edges": [], "error": "Vista grafo non riconosciuta"}


@router.put("/api/people/{node_id}")
def update_person(node_id: str, request: PersonUpdate):
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase non connesso")
    if node_id == "user_self":
        raise HTTPException(status_code=400, detail="Il nodo principale non è modificabile")
    payload = request.model_dump(exclude_unset=True)
    payload.update({"type": "person", "manually_edited": True})
    result = supabase.table("nodes").update(payload).eq("id", node_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    return result.data[0]


@router.delete("/api/people/{node_id}")
def delete_person(node_id: str):
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase non connesso")
    if node_id == "user_self":
        raise HTTPException(status_code=400, detail="Il nodo principale non è eliminabile")
    node = supabase.table("nodes").select("id").eq("id", node_id).execute().data
    if not node:
        raise HTTPException(status_code=404, detail="Persona non trovata")
    supabase.table("edges").delete().eq("source", node_id).execute()
    supabase.table("edges").delete().eq("target", node_id).execute()
    supabase.table("nodes").delete().eq("id", node_id).execute()
    return {"status": "deleted", "id": node_id}


@router.put("/api/memory-facts/{fact_id}")
def update_memory_fact(fact_id: str, request: FactUpdate):
    if not supabase:
        raise HTTPException(status_code=503, detail="Supabase non connesso")
    topics = list(dict.fromkeys(str(topic).strip() for topic in request.topics if str(topic).strip()))
    result = supabase.table("user_facts").update({"fact": request.fact.strip(), "topics": topics}).eq("id", fact_id).execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Memoria non trovata")
    return result.data[0]
