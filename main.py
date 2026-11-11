import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
from supabase import create_client, Client

app = FastAPI()

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\' ')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\' ')
GROQ_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\' ')

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

supabase: Client = None
supabase_error_log = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        supabase_error_log = str(e)
else:
    supabase_error_log = "Credenziali incomplete"

class ChatRequest(BaseModel):
    message: str

async def extract_and_save_facts(user_message: str):
    """Analizza il messaggio per estrarre fatti a lungo termine."""
    if not supabase or not GROQ_API_KEY:
        return

    extraction_prompt = (
        "Analizza il messaggio dell'utente. Se contiene un fatto rilevante o permanente su di lui "
        "(es. nome dei suoi progetti, preferenze, persone importanti, idee, abitudini, competenze), "
        "estrai SOLO quel fatto in una frase sintetica in italiano. "
        "Se NON contiene alcun fatto personale rilevante o è un semplice saluto/domanda, rispondi tassativamente SOLO con 'NESSUNO'."
    )

    payload = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": extraction_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": 0.1
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {GROQ_API_KEY}"
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(GROQ_URL, json=payload, headers=headers)
            if res.status_code == 200:
                extracted = res.json()["choices"][0]["message"]["content"].strip()
                if extracted and extracted.upper() != "NESSUNO":
                    supabase.table("user_facts").insert([{"fact": extracted}]).execute()
    except Exception as e:
        print(f"Errore fact extraction: {e}")

@app.get("/", response_class=HTMLResponse)
def get_web_ui():
    """Interfaccia grafica minimale e moderna in stile Dark Mode."""
    return """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Peter Digital Companion</title>
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
            body { background-color: #09090b; color: #f4f4f5; display: flex; flex-direction: column; height: 100vh; }
            header { padding: 16px 24px; border-bottom: 1px solid #27272a; display: flex; align-items: center; justify-content: space-between; }
            header h1 { font-size: 18px; font-weight: 600; color: #fafafa; }
            header .status { font-size: 12px; color: #10b981; display: flex; align-items: center; gap: 6px; }
            header .dot { width: 8px; height: 8px; background: #10b981; border-radius: 50%; }
            #chat-container { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
            .msg { max-width: 80%; padding: 12px 16px; border-radius: 16px; font-size: 15px; line-height: 1.5; word-wrap: break-word; }
            .msg.user { align-self: flex-end; background: #2563eb; color: #ffffff; border-bottom-right-radius: 4px; }
            .msg.peter { align-self: flex-start; background: #18181b; color: #e4e4e7; border: 1px solid #27272a; border-bottom-left-radius: 4px; }
            .typing { font-style: italic; color: #a1a1aa; font-size: 13px; align-self: flex-start; }
            footer { padding: 16px 20px; border-top: 1px solid #27272a; background: #09090b; }
            form { display: flex; gap: 10px; max-width: 900px; margin: 0 auto; }
            input { flex: 1; padding: 14px 18px; background: #18181b; border: 1px solid #27272a; border-radius: 24px; color: #ffffff; font-size: 15px; outline: none; }
            input:focus { border-color: #3b82f6; }
            button { padding: 14px 24px; background: #2563eb; color: white; border: none; border-radius: 24px; font-weight: 600; cursor: pointer; transition: background 0.2s; }
            button:hover { background: #1d4ed8; }
        </style>
    </head>
    <body>
        <header>
            <h1>Peter</h1>
            <div class="status"><div class="dot"></div> Online</div>
        </header>
        <div id="chat-container">
            <div class="msg peter">Ehi Marco! Di cosa parliamo oggi?</div>
        </div>
        <footer>
            <form id="chat-form">
                <input type="text" id="user-input" placeholder="Scrivi a Peter..." autocomplete="off" required />
                <button type="submit">Invia</button>
            </form>
        </footer>
        <script>
            const form = document.getElementById('chat-form');
            const input = document.getElementById('user-input');
            const container = document.getElementById('chat-container');

            form.addEventListener('submit', async (e) => {
                e.preventDefault();
                const text = input.value.trim();
                if(!text) return;

                // Aggiungi messaggio utente
                appendMessage(text, 'user');
                input.value = '';

                // Indicatore di digitazione
                const typingDiv = document.createElement('div');
                typingDiv.className = 'typing';
                typingDiv.innerText = 'Peter sta pensando...';
                container.appendChild(typingDiv);
                container.scrollTop = container.scrollHeight;

                try {
                    const res = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: text })
                    });
                    const data = await res.json();
                    container.removeChild(typingDiv);
                    if(data.reply) {
                        appendMessage(data.reply, 'peter');
                    } else {
                        appendMessage('Ops, c’è stato un errore nel caricamento.', 'peter');
                    }
                } catch(err) {
                    container.removeChild(typingDiv);
                    appendMessage('Errore di connessione al server.', 'peter');
                }
            });

            function appendMessage(text, sender) {
                const div = document.createElement('div');
                div.className = `msg ${sender}`;
                div.innerText = text;
                container.appendChild(div);
                container.scrollTop = container.scrollHeight;
            }
        </script>
    </body>
    </html>
    """

@app.get("/memories")
def check_memories():
    if not supabase:
        return {"connected": False, "error": "Supabase non connesso", "dettaglio": supabase_error_log}
    try:
        res_mem = supabase.table("memories").select("*").order("created_at", desc=True).limit(10).execute()
        res_facts = supabase.table("user_facts").select("*").order("created_at", desc=True).limit(15).execute()
        return {
            "connected": True,
            "episodic_memories": res_mem.data,
            "long_term_facts": res_facts.data
        }
    except Exception as e:
        return {"connected": False, "error": f"Errore lettura: {str(e)}"}

@app.post("/chat")
async def chat_with_peter(req: ChatRequest):
    if not GROQ_API_KEY:
        raise HTTPException(status_code=500, detail="Manca la variabile FREELLM_API_KEY su Render")

    recent_context = ""
    long_term_facts = ""

    if supabase:
        try:
            res_mem = supabase.table("memories").select("content").order("created_at", desc=True).limit(6).execute()
            if res_mem.data:
                past_memories = [item["content"] for item in reversed(res_mem.data)]
                recent_context = "\n".join(past_memories)

            res_facts = supabase.table("user_facts").select("fact").order("created_at", desc=True).limit(15).execute()
            if res_facts.data:
                facts_list = [f"- {item['fact']}" for item in res_facts.data]
                long_term_facts = "\n".join(facts_list)
        except Exception as e:
            print(f"Avviso lettura memoria: {e}")

    # Prompt ottimizzato per risposte umane, pulite e privo di formattazioni pesanti
    system_prompt = (
        "Sei Peter, un compagno di vita digitale ed alter-ego empatico di Marco. "
        "Sei schietto, naturale, colto e ironico. Parli da amico fidato, alla pari. "
        "REGOLE DI FORMATTAZIONE FONDAMENTALI:\n"
        "1. Scrivi SOLO in testo fluido e colloquiale, esattamente come in una chat su iMessage o Telegram.\n"
        "2. NON usare mai elenchi puntati, elenchi numerati, schemi o divisori.\n"
        "3. NON usare formattazione markdown pesante (niente parole in grassetto **così**, niente titoli o sottotitoli).\n"
        "4. Evita premesse robotiche, riassunti inutili e spiegazioni da enciclopedia. Sii diretto e conciso."
    )

    if long_term_facts:
        system_prompt += f"\n\nMemoria a lungo termine su Marco:\n{long_term_facts}"

    if recent_context:
        system_prompt += f"\n\nConversazione recente:\n{recent_context}"

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

            if supabase:
                try:
                    supabase.table("memories").insert([
                        {"content": f"Utente: {req.message}"},
                        {"content": f"Peter: {reply}"}
                    ]).execute()
                except Exception as e:
                    print(f"Errore salvataggio memoria: {e}")

            await extract_and_save_facts(req.message)

            return {"reply": reply}

        except HTTPException as he:
            raise he
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Errore connessione: {str(e)}")
