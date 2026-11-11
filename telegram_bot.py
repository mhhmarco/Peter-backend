import httpx
from config import TELEGRAM_BOT_TOKEN
from database import get_recent_memories, get_long_term_facts, save_episodic_memory
from llm import generate_peter_response, extract_and_save_facts

async def process_telegram_update(update: dict):
    if not TELEGRAM_BOT_TOKEN or "message" not in update or "text" not in update["message"]:
        return

    chat_id = update["message"]["chat"]["id"]
    user_text = update["message"]["text"]

    recent_context = get_recent_memories(limit=6)
    long_term_facts = get_long_term_facts(limit=15)

    result = await generate_peter_response(user_text, recent_context, long_term_facts)
    reply = result["reply"]

    save_episodic_memory(user_text, reply)
    await extract_and_save_facts(user_text)

    # Pulizia rigorosa del token da spazi o a capo accidentali
    clean_token = TELEGRAM_BOT_TOKEN.strip()
    telegram_url = f"https://api.telegram.org/bot{clean_token}/sendMessage"
    
    async with httpx.AsyncClient() as client:
        await client.post(telegram_url, json={"chat_id": chat_id, "text": reply})
