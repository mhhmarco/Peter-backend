import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\' ')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\' ')
GROQ_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\' ')
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip('"\' ')
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip('"\' ')

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
