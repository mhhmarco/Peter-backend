def calculate_galaxy_layout(supabase_client) -> dict:
    nodes = []
    edges = []

    if not supabase_client:
        return {
            "nodes": [{
                "id": "user_self", 
                "name": "Marco (Tu)", 
                "type": "core", 
                "category": "core", 
                "notes": "Admin & Core Neural Center",
                "gender": "M",
                "birth_year": 2006
            }],
            "edges": []
        }

    try:
        res_nodes = supabase_client.table("nodes").select("*").execute()
        if res_nodes.data:
            nodes = res_nodes.data
        else:
            nodes = [{
                "id": "user_self", 
                "name": "Marco (Tu)", 
                "type": "core", 
                "category": "core", 
                "notes": "Admin & Core Neural Center",
                "gender": "M",
                "birth_year": 2006
            }]
    except Exception as e:
        print(f"Errore lettura nodes: {e}")
        nodes = [{
            "id": "user_self", 
            "name": "Marco (Tu)", 
            "type": "core", 
            "category": "core", 
            "notes": "Admin & Core Neural Center",
            "gender": "M",
            "birth_year": 2006
        }]

    try:
        res_edges = supabase_client.table("edges").select("*").execute()
        if res_edges.data:
            edges = res_edges.data
    except Exception as e:
        print(f"Errore lettura edges: {e}")

    return {"nodes": nodes, "edges": edges}
