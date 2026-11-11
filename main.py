import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from supabase import create_client, Client

app = FastAPI()

# Variabili d'ambiente pulite
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\' ')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\' ')
GROQ_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\' ')

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Inizializzazione Supabase con tracciamento errori
supabase: Client = None
supabase_error_log = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_error_log = str(e)
        print(f"Errore inizializzazione Supabase: {e}")
else:
    supabase_error_log = f"Credenziali incomplete (URL present: {bool(SUPABASE_URL)}, KEY present: {bool(SUPABASE_KEY)})"

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def health_check():
    return {"status": "online", "agent": "Peter"}

@app.get("/memories")
def check_memories():
    if not supabase:
        return {
            "connected": False,
            "error": "Supabase non connesso",
            "dettaglio": supabase_error_log
        }
    try:
        res_mem = supabase.table("memories").select("*").order("created_at", desc=True).limit(5).execute()
        res_facts = supabase.table("user_facts").select("*").limit(10).execute()
        return {
            "connected": True,
            "episodic_memories": res_mem.data,
            "long_term_facts": res_facts.data
        }
    except Exception as e:
        return {"connected": False, "error": f"Errore lettura tabelle: {str(e)}"}

@app.post("/chat")
async def chat_with_peter(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca la variabile FREELLM_API_KEY su Render")

    # 1. Recupero Memoria Episodica e Fatti a Lungo Termine
    recent_context = ""
    long_term_facts = ""

    if supabase:
        try:
            # Memoria di lavoro recente
            res_mem = supabase.table("memories").select("content").order("created_at", desc=True).limit(6).execute()
            if res_mem.data:
                past_memories = [item["content"] for item in reversed(res_mem.data)]
                recent_context = "\n".join(past_memories)

            # Fatti fondamentali su Marco
            res_facts = supabase.table("user_facts").select("fact").limit(15).execute()
            if res_facts.data:
                facts_list = [f"- {item['fact']}" for item in res_facts.data]
                long_term_facts = "\n".join(facts_list)
        except Exception as e:
            print(f"Avviso lettura memoria: {e}")

    # 2. System Prompt Personalizzato
    system_prompt = (
        "Sei Peter, un compagno di vita digitale ed alter-ego empatico. "
        "Non sei un assistente virtuale formale né un chatbot esecutivo. "
        "Comportati come un amico fidato, schietto, empatico e alla pari. "
        "Il tuo tono è colloquiale, naturale, colto e ironico al momento giusto. "
        "NON fare premesse robotiche, NON fare riassunti inutili."
    )

    if long_term_facts:
        system_prompt += f"\n\nFatti chiave su Marco che ricordi a lungo termine:\n{long_term_facts}"

    if recent_context:
        system_prompt += f"\n\nEstratto recente della conversazione:\n{recent_context}"

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Errore Groq ({res.status_code}): {res.text}")
            
            data = res.json()
            reply = data["choices"][0]["message"]["content"]

            # 3. Salvataggio in memoria episodica
            if supabase:
                try:
                    supabase.table("memories").insert([
                        {"content": f"Utente: {req.message}"},
                        {"content": f"Peter: {reply}"}
                    ]).execute()
                except Exception as e:
                    print(f"Errore salvataggio memoria: {e}")

            return {"reply": reply}

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore connessione: {str(e)}")
