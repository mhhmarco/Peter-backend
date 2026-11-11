def save_contact(name: str, category: str, details: str, notes: str):
    if not supabase:
        return
    try:
        supabase.table("contacts").insert([{
            "name": name,
            "category": category, # famiglia, amicizia, lavoro
            "details": details,
            "notes": notes
        }]).execute()
    except Exception as e:
        print(f"Errore salvataggio contatto: {e}")

def get_all_contacts():
    if not supabase:
        return []
    try:
        res = supabase.table("contacts").select("*").execute()
        return res.data or []
    except Exception as e:
        return []

def save_calendar_event(title: str, date: str, description: str):
    if not supabase:
        return
    try:
        supabase.table("calendar_events").insert([{
            "title": title,
            "date": date,
            "description": description
        }]).execute()
    except Exception as e:
        print(f"Errore salvataggio evento: {e}")
