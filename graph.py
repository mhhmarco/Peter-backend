import math

def calculate_galaxy_layout(supabase_client) -> dict:
    """
    Organizza i nodi in 4 zone galattiche distinte attorno al Core (Marco):
    - Zona Ciano (Persone & Relazioni)
    - Zona Viola (Memorie di Chat & Fatti)
    - Zona Rosa (Eventi personali)
    - Zona Gialla / Ambra (Interessi ricorrenti)
    """
    nodes = [{
        "id": "user_self", 
        "name": "Marco (Tu)", 
        "category": "core", 
        "type": "core", 
        "x": 0, "y": 0, "z": 0, 
        "notes": "Admin & Core Neural Center di Peter OS"
    }]
    edges = []

    if not supabase_client:
        return {"nodes": nodes, "edges": edges}

    try:
        # 1. ZONA PERSONE (Ciano - in alto a sinistra / sinistra)
        contacts = supabase_client.table("contacts").select("*").execute().data or []
        for idx, c in enumerate(contacts):
            node_id = f"contact_{c.get('id', idx)}"
            angle = (idx / max(len(contacts), 1)) * math.pi - (math.pi / 2)
            dist = 240 + (idx % 3) * 35
            nodes.append({
                "id": node_id,
                "name": c.get("name", "Persona"),
                "category": c.get("category", "amicizia"),
                "type": "person",
                "x": math.cos(angle) * dist - 180,
                "y": math.sin(angle) * dist - 120,
                "z": (idx % 2) * 40 - 20,
                "notes": c.get("notes", "Nessuna nota"),
                "details": c.get("details", "")
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    try:
        # 2. ZONA MEMORIE / CHAT (Viola - centro-basso)
        facts = supabase_client.table("user_facts").select("*").limit(45).execute().data or []
        for idx, f in enumerate(facts):
            node_id = f"fact_{f.get('id', idx)}"
            angle = (idx / max(len(facts), 1)) * (2 * math.pi)
            dist = 180 + ((idx * 13) % 100)
            nodes.append({
                "id": node_id,
                "name": f.get("fact", "")[:28] + "...",
                "category": "memory",
                "type": "memory",
                "x": math.cos(angle) * dist,
                "y": math.sin(angle) * dist + 160,
                "z": ((idx % 3) - 1) * 50,
                "notes": f.get("fact", ""),
                "details": f"Registrato il: {f.get('created_at', '')[:10]}"
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    try:
        # 3. ZONA EVENTI PERSONALI (Rosa - a destra)
        events = supabase_client.table("calendar_events").select("*").limit(25).execute().data or []
        for idx, e in enumerate(events):
            node_id = f"event_{e.get('id', idx)}"
            angle = (idx / max(len(events), 1)) * math.pi + (math.pi / 4)
            dist = 280 + (idx % 2) * 50
            nodes.append({
                "id": node_id,
                "name": e.get("title", "Evento")[:24],
                "category": "event",
                "type": "event",
                "x": math.cos(angle) * dist + 220,
                "y": math.sin(angle) * dist - 60,
                "z": (idx % 2) * 30,
                "notes": e.get("description", "Nessuna descrizione"),
                "details": f"Stato: {e.get('start_time', '')}"
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    try:
        # 4. ZONA INTERESSI RICORRENTI (Ambra/Giallo - in alto / alone esterno)
        interests = supabase_client.table("interests").select("*").limit(30).execute().data or []
        for idx, i in enumerate(interests):
            node_id = f"interest_{i.get('id', idx)}"
            angle = (idx / max(len(interests), 1)) * (2 * math.pi)
            dist = 400 + (idx % 4) * 30
            nodes.append({
                "id": node_id,
                "name": i.get("name", "Interesse")[:26],
                "category": "interest",
                "type": "interest",
                "x": math.cos(angle) * dist,
                "y": math.sin(angle) * dist - 300,
                "z": ((idx % 2) * 60) - 30,
                "notes": i.get("description", "Interesse ricorrente dell'utente"),
                "details": "Categoria: Interessi & Skill"
            })
            edges.append({"source": "user_self", "target": node_id})
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}
