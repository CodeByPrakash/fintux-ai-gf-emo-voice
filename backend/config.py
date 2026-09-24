import os
import pathlib
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(dotenv_path=pathlib.Path(__file__).parent.parent / ".env")

OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
raw_host = os.getenv("OLLAMA_HOST", "https://ollama.com" if OLLAMA_API_KEY else "http://localhost:11434").strip()

# Normalize host URL (strip trailing /api/chat, /api, or trailing slashes)
for suffix in ["/api/chat", "/api", "/"]:
    if raw_host.endswith(suffix):
        raw_host = raw_host[:-len(suffix)]

OLLAMA_HOST = raw_host
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b-cloud")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

BASE_DIR = pathlib.Path(__file__).parent
PERSONA_DIR = BASE_DIR / "persona"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "fenry.db"
CHROMA_PATH = str(DATA_DIR / "chroma_v2")
