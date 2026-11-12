import httpx
from icalendar import Calendar

def parse_vcard(vcf_text: str) -> list:
    contacts = []
    current_contact = {}
    for line in vcf_text.splitlines():
        line = line.strip()
        if line.startswith("BEGIN:VCARD"):
            current_contact = {"name": "", "category": "amicizia", "notes": "", "gender": "sconosciuto", "birth_year": None, "relation_type": "neutrale"}
        elif line.startswith("FN:") or line.startswith("N:"):
            name_val = line.split(":", 1)[1].replace(";", " ").strip()
            if name_val and not current_contact.get("name"):
                current_contact["name"] = name_val
        elif line.startswith("NOTE:"):
            current_contact["notes"] = line.split(":", 1)[1].strip()
        elif line.startswith("END:VCARD"):
            if current_contact.get("name"):
                contacts.append(current_contact)
            current_contact = {}
    return contacts

async def fetch_and_parse_ical(url: str) -> list:
    events = []
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                cal = Calendar.from_ical(res.content)
                for component in cal.walk('vevent'):
                    title = str(component.get('summary', 'Evento'))
                    desc = str(component.get('description', ''))
                    start = component.get('dtstart')
                    start_str = start.dt.strftime('%Y-%m-%d %H:%M') if start else 'Programmato'
                    events.append({"title": title, "description": desc, "start_time": start_str})
    except Exception as e:
        print(f"Errore parsing iCal: {e}")
    return events
