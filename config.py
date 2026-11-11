import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip('"\' ')
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip('"\' ')
GROQ_API_KEY = os.getenv("FREELLM_API_KEY", "").strip('"\' ')

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-120b"
