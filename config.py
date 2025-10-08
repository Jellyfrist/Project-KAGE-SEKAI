import os
from dotenv import load_dotenv
load_dotenv()

MODEL = os.getenv("MODEL")
assert MODEL, "Set MODEL in .env (e.g., groq/openai/gpt-oss-120b)"

EMBED_MODEL = os.getenv("EMBED_MODEL")
assert MODEL, "Set EMBED_MODEL in .env (e.g., groq/openai/gpt-oss-120b)"
