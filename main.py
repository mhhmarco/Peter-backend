import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from supabase import create_client, Client

app = FastAPI()

# Variabili d'ambiente
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\'' )
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\'' )
GROQ_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\'' )

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Inizializzazione Supabase
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Avviso Supabase: {e}")

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def health_check():
    return {"status": "online", "agent": "Peter"}

@app.get("/memories")
def check_memories():
    if not supabase:
        return {"error": "Supabase non connesso"}
    try:
        res = supabase.table("memories").select("*").order("created_at", desc=True).limit(10).execute()
        return {"count": len(res.data), "memories": res.data}
    except Exception as e:
        return {"error": str(e)}

@app.post("/chat")
async def chat_with_peter(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="Manca la variabile FREELLM_API_KEY su Render"
        )

    # 1. Recupero degli ultimi ricordi
    recent_context = ""
    if supabase:
        try:
            res = supabase.table("memories").select("content").order("created_at", desc=True).limit(6).execute()
            if res.data:
                past_memories = [item["content"] for item in reversed(res.data)]
                recent_context = "\n".join(past_memories)
        except Exception as e:
            print(f"Errore lettura memoria: {e}")

    # 2. System Prompt
    system_prompt = (
        "Sei Peter, un compagno di vita digitale ed alter-ego empatico. "
        "Non sei un assistente virtuale formale né un chatbot esecutivo. "
        "Comportati come un amico fidato, schietto, empatico e alla pari. "
        "Il tuo tono è colloquiale, naturale, colto e ironico al momento giusto. "
        "NON fare premesse robotiche, NON fare riassunti inutili."
    )

    if recent_context:
        system_prompt += f"\n\nEcco alcuni tuoi ricordi e messaggi recenti scambiati con l'utente:\n{recent_context}"

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
                raise HTTPException(
                    status_code=500, 
                    detail=f"Errore Groq ({res.status_code}): {res.text}"
                )
            
            data = res.json()
            reply = data["choices"][0]["message"]["content"]

            # 3. Salvataggio della memoria
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
