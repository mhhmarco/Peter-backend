import httpx
from fastapi import BackgroundTasks
from config import TELEGRAM_BOT_TOKEN
from database import get_recent_memories, get_long_term_facts, save_episodic_memory
from llm import generate_peter_response, process_background_memory

async def process_telegram_update(update: dict, background_tasks: BackgroundTasks):
    if not TELEGRAM_BOT_TOKEN or "message" not in update or "text" not in update["message"]:
        return

    chat_id = update["message"]["chat"]["id"]
    user_text = update["message"]["text"]

    recent_context = get_recent_memories(limit=6)
    long_term_facts = get_long_term_facts(limit=15)

    result = await generate_peter_response(user_text, recent_context, long_term_facts)
    reply = result["reply"]
    media = result.get("media")

    # Formattazione media per messaggio Telegram
    if media and media.get("embed_url"):
        embed_url = media["embed_url"]
        if "youtube" in embed_url:
            video_id = embed_url.split("/")[-1].split("?")[0]
            reply += f"\n\n🎬 Video trovato: https://www.youtube.com/watch?v={video_id}"
        elif "applemusic" in embed_url:
            reply += f"\n\n🎵 {media.get('title', 'Apri su Apple Music')}"

    save_episodic_memory(user_text, reply)
    
    # Task asincrono in background per estrazione fatti/grafo da Telegram
    background_tasks.add_task(process_background_memory, user_text)

    clean_token = TELEGRAM_BOT_TOKEN.strip()
    telegram_url = f"https://api.telegram.org/bot{clean_token}/sendMessage"

    async with httpx.AsyncClient() as client:
        await client.post(telegram_url, json={"chat_id": chat_id, "text": reply})

