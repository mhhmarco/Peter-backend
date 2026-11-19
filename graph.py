from __future__ import annotations

from typing import Any


_FAMILY_TERMS = (
    "famiglia", "familiare", "padre", "madre", "genitore", "figlio", "figlia",
    "fratello", "sorella", "nonno", "nonna", "zio", "zia", "cugino", "cugina",
    "nipote", "marito", "moglie", "coniuge", "partner", "suocero", "suocera", "cognato", "cognata",
)


def _text(value: Any) -> str:
    return str(value or "").strip().casefold()


def _is_family(node: dict) -> bool:
    category = _text(node.get("category"))
    relation = _text(node.get("relation_type"))
    return category in {"famiglia", "family"} or any(
        term in relation or term in category for term in _FAMILY_TERMS
    )


def _core_node() -> dict:
    # Ancora il nodo centrale Marco alle coordinate (0, 0, 0) per mantenere sempre centrato il grafo 3D
    return {
        "id": "user_self", "name": "Marco (Tu)", "type": "core",
        "category": "core", "notes": "Admin & Core Neural Center",
        "gender": "M", "birth_year": 2006,
        "fx": 0, "fy": 0, "fz": 0,
    }


def calculate_galaxy_layout(supabase_client) -> dict:
    """Return Nexus nodes/links, including explicit family-tree parent and spouse links.

    Family edges are directed from parent to child (or between spouses) and trace
    genealogically back to Marco (user_self). No family relationship is guessed.
    """
    if not supabase_client:
        return {"nodes": [_core_node()], "edges": []}

    try:
        result = supabase_client.table("nodes").select("*").execute()
        nodes = result.data or []
    except Exception as exc:
        print(f"Errore lettura nodes: {exc}")
        nodes = []

    if not nodes:
        nodes = [_core_node()]

    normalized_nodes = []
    ids = set()
    name_to_id = {"marco": "user_self", "marco (tu)": "user_self", "io": "user_self"}
    has_core = False

    for original in nodes:
        node = dict(original)
        node_id = str(node.get("id", ""))
        if not node_id:
            continue
        node["id"] = node_id
        ids.add(node_id)
        if node_id == "user_self" or node.get("type") == "core":
            has_core = True
            # Fissa il nodo centrale all'origine 3D in ogni vista
            node["fx"] = 0
            node["fy"] = 0
            node["fz"] = 0
        if node.get("type") == "person":
            family = _is_family(node)
            node["category"] = "famiglia" if family else "amicizia"
            node["relationship_group"] = "family" if family else "friend"
            name_to_id[_text(node.get("name"))] = node_id
        normalized_nodes.append(node)

    if not has_core:
        normalized_nodes.insert(0, _core_node())
        ids.add("user_self")

    try:
        result = supabase_client.table("edges").select("*").execute()
        edges = [dict(edge) for edge in (result.data or [])]
    except Exception as exc:
        print(f"Errore lettura edges: {exc}")
        edges = []

    edge_keys = set()
    for edge in edges:
        source, target = str(edge.get("source", "")), str(edge.get("target", ""))
        edge["source"], edge["target"] = source, target
        relation = _text(edge.get("relation_type"))
        edge["category"] = "famiglia" if any(term in relation for term in _FAMILY_TERMS) else edge.get("category", "relazione")
        edge_keys.add((source, target))

    # The migration adds parent_node_id. parent_id and parent_name are also accepted
    # so parent-child edges always point directly from parent to child.
    for node in normalized_nodes:
        if node.get("type") != "person":
            continue
        parent = node.get("parent_node_id") or node.get("parent_id")
        if not parent and node.get("parent_name"):
            parent = name_to_id.get(_text(node["parent_name"]))
        if parent:
            parent = str(parent)
            if parent in ids and parent != node["id"] and (parent, node["id"]) not in edge_keys:
                edges.append({
                    "source": parent, "target": node["id"],
                    "relation_type": node.get("family_relation") or "genitore-figlio",
                    "category": "famiglia", "family_tree": True,
                })
                edge_keys.add((parent, node["id"]))

    return {"nodes": normalized_nodes, "edges": edges}
