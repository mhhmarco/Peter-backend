def calculate_galaxy_layout(supabase_client) -> dict:
    nodes = [{
        "id": "user_self", 
        "name": "Marco (Tu)", 
        "category": "core", 
        "type": "core", 
        "notes": "Admin & Core Neural Center di Peter OS",
        "gender": "M",
        "birth_year": 2006
    }]
    edges = []

    if not supabase_client:
        return {"nodes": nodes, "edges": edges}

    # 1. ZONA PERSONE (Escludendo eventuali doppioni dell'utente stesso)
    try:
        contacts = supabase_client.table("contacts").select("*").execute().data or []
        for idx, c in enumerate(contacts):
            c_name = c.get("name", "Persona").strip()
            if c_name.lower() in ["marco", "barbi", "marco barbiero", "marco barbiero torres"]:
                continue
            node_id = f"contact_{c.get('id', idx)}"
            nodes.append({
                "id": node_id,
                "name": c_name,
                "category": c.get("category", "amicizia"),
                "type": "person",
                "notes": c.get("notes", "Nessuna nota"),
                "details": c.get("details", ""),
                "gender": c.get("gender", "sconosciuto"),
                "birth_year": c.get("birth_year"),
                "relation_type": c.get("relation_type", "neutrale")
            })
            edges.append({
                "source": "user_self", 
                "target": node_id, 
                "relation_type": c.get("relation_type", "neutrale")
            })
    except Exception as e:
        print(f"Errore graph contatti: {e}")

    # 2. ZONA MEMORIE
    try:
        facts = supabase_client.table("user_facts").select("*").limit(45).execute().data or []
        for idx, f in enumerate(facts):
            node_id = f"fact_{f.get('id', idx)}"
            nodes.append({
                "id": node_id,
                "name": f.get("fact", "")[:32] + "...",
                "category": "memory",
                "type": "memory",
                "notes": f.get("fact", ""),
                "details": f"Registrato il: {f.get('created_at', '')[:10]}"
            })
            edges.append({"source": "user_self", "target": node_id, "relation_type": "memoria"})
    except Exception:
        pass

    # 3. ZONA EVENTI
    try:
        events = supabase_client.table("calendar_events").select("*").limit(25).execute().data or []
        for idx, e in enumerate(events):
            node_id = f"event_{e.get('id', idx)}"
            nodes.append({
                "id": node_id,
                "name": e.get("title", "Evento")[:26],
                "category": "event",
                "type": "event",
                "notes": e.get("description", "Nessuna descrizione"),
                "details": f"Stato: {e.get('start_time', '')}"
            })
            edges.append({"source": "user_self", "target": node_id, "relation_type": "evento"})
    except Exception:
        pass

    # 4. ZONA INTERESSI
    try:
        interests = supabase_client.table("interests").select("*").limit(30).execute().data or []
        for idx, i in enumerate(interests):
            node_id = f"interest_{i.get('id', idx)}"
            nodes.append({
                "id": node_id,
                "name": i.get("name", "Interesse")[:26],
                "category": "interest",
                "type": "interest",
                "notes": i.get("description", "Interesse ricorrente dell'utente"),
                "details": "Passione / Attitudine"
            })
            edges.append({"source": "user_self", "target": node_id, "relation_type": "passione"})
    except Exception:
        pass

    return {"nodes": nodes, "edges": edges}
