import yaml
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import BACKEND_PORT, PERSONA_DIR
from models.database import init_db
from core.neural_engine import NeuralEngine
from core.llm import ollama_client
from routers import chat, persona, memory, analytics


def load_persona() -> dict:
    path = PERSONA_DIR / "gf_model.yaml"
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"name": "FENRY", "style": {"tone": "gentle, playful"}, "affection_level": 0.8}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n===== FENRY-GF Neural Engine v1.0 =====\n")

    await init_db()
    print("[DB] SQLite initialized")

    persona_data = load_persona()
    engine = NeuralEngine(persona_data)
    chat.set_engine(engine)
    print(f"[PERSONA] Loaded: {persona_data.get('name', 'FENRY')}")

    status = await ollama_client.check_connection()
    if status.get("cloud") and status.get("rest"):
        print(f"[LLM] Connected to Ollama Cloud -- model: {status['model']}")
    elif status.get("library"):
        print(f"[LLM] Connected via library -- model: {status['model']}")
    elif status.get("rest"):
        print(f"[LLM] Connected via REST API -- model: {status['model']}")
    else:
        print("[LLM] WARNING: Ollama not available! Check OLLAMA_API_KEY in .env")

    print(f"\n[SERVER] http://localhost:{BACKEND_PORT}")
    print("[SERVER] WebSocket: ws://localhost:{}/ws/chat\n".format(BACKEND_PORT))

    yield

    print("\n[SERVER] Shutting down...")


app = FastAPI(title="FENRY-GF", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(persona.router)
app.include_router(memory.router)
app.include_router(analytics.router)


@app.get("/api/health")
async def health():
    status = await ollama_client.check_connection()
    return {"status": "ok", "ollama": status}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=BACKEND_PORT, reload=True)
