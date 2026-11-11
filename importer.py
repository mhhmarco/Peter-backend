import re
import httpx

def parse_vcard(vcard_text: str) -> list:
    """Estrae contatti da file .vcf (vCard)."""
    contacts = []
    blocks = vcard_text.split("END:VCARD")
    for b in blocks:
        name_match = re.search(r'(?:FN|N)(?:;[^:]*)?:(.*)', b)
        tel_match = re.search(r'TEL(?:;[^:]*)?:(.*)', b)
        note_match = re.search(r'NOTE(?:;[^:]*)?:(.*)', b)
        
        if name_match:
            raw_name = name_match.group(1).replace(';', ' ').strip()
            if raw_name:
                tel = tel_match.group(1).strip() if tel_match else ""
                note = note_match.group(1).strip() if note_match else ""
                contacts.append({
                    "name": raw_name,
                    "category": "amicizia",
                    "details": tel,
                    "notes": note
                })
    return contacts

async def fetch_and_parse_ical(ical_url: str) -> list:
    """Scarica ed estrae eventi da un link iCal pubblico (.ics)."""
    events = []
    if not ical_url.startswith("http"):
        ical_url = "https://" + ical_url
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            res = await client.get(ical_url)
            if res.status_code == 200:
                text = res.text
                vevents = text.split("END:VEVENT")
                for ev in vevents:
                    sum_match = re.search(r'SUMMARY:(.*)', ev)
                    dt_match = re.search(r'DTSTART(?:;[^:]*)?:(.*)', ev)
                    desc_match = re.search(r'DESCRIPTION:(.*)', ev)
                    if sum_match:
                        title = sum_match.group(1).strip()
                        date_str = dt_match.group(1).strip() if dt_match else ""
                        desc = desc_match.group(1).strip() if desc_match else ""
                        events.append({
                            "title": title,
                            "date": date_str,
                            "description": desc
                        })
    except Exception as e:
        print(f"Errore download/parsing iCal {ical_url}: {e}")
    return events
