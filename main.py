import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from supabase import create_client, Client

app = FastAPI()

# Variabili d'ambiente con pulizia di spazi e virgolette
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\' ')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\' ')
FREELLM_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\' ')

# URL Groq predefinito pulito
FREELLM_URL = os.getenv("FREELLM_URL", "https://api.groq.com/openai/v1/chat/completions").strip('"\' ')
if not FREELLM_URL:
    FREELLM_URL = "https://api.groq.com/openai/v1/chat/completions"

# Supabase Client
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

@app.post("/chat")
async def chat_with_peter(req: ChatRequest):
    system_prompt = (
        "Sei Peter, un compagno di vita digitale ed alter-ego empatico. "
        "Non sei un assistente virtuale formale né un chatbot esecutivo. "
        "Comportati come un amico fidato, schietto, empatico e alla pari. "
        "Il tuo tono è colloquiale, naturale, colto e ironico al momento giusto. "
        "NON fare premesse robotiche, NON fare riassunti inutili."
    )
    
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": req.message}
        ]
    }
    
    headers = {"Content-Type": "application/json"}
    if FREELLM_API_KEY:
        headers["Authorization"] = f"Bearer {FREELLM_API_KEY}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(FREELLM_URL, json=payload, headers=headers)
            res.raise_for_status()
            data = res.json()
            return {"reply": data["choices"][0]["message"]["content"]}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore generazione: {str(e)}")
