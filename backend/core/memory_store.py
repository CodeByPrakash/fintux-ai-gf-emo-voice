import uuid
import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHROMA_PATH


class MemoryStore:
    """ChromaDB-backed vector memory for persistent context."""

    def __init__(self):
        self._client = None
        self._collection = None

    def _ensure_init(self):
        if self._client is None:
            try:
                import chromadb
                from chromadb.config import Settings
                self._client = chromadb.PersistentClient(
                    path=CHROMA_PATH,
                    settings=Settings(anonymized_telemetry=False)
                )
                self._collection = self._client.get_or_create_collection(
                    name="fenry_memories",
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                import shutil
                print(f"[MEMORY] ChromaDB migration issue: {e}. Rebuilding collection store...")
                try:
                    backup_path = f"{CHROMA_PATH}_legacy_{int(time.time())}"
                    if os.path.exists(CHROMA_PATH):
                        shutil.move(CHROMA_PATH, backup_path)
                    import chromadb
                    from chromadb.config import Settings
                    self._client = chromadb.PersistentClient(
                        path=CHROMA_PATH,
                        settings=Settings(anonymized_telemetry=False)
                    )
                    self._collection = self._client.get_or_create_collection(
                        name="fenry_memories",
                        metadata={"hnsw:space": "cosine"}
                    )
                except Exception as inner_e:
                    print(f"[MEMORY] ChromaDB init fallback: {inner_e}")
                    self._collection = None

    def add(self, content: str, tags: list = None, metadata: dict = None) -> str:
        self._ensure_init()
        if not self._collection:
            return ""
        mem_id = str(uuid.uuid4())
        meta = {
            "tags": ",".join(tags or []),
            "timestamp": str(time.time()),
            **(metadata or {})
        }
        self._collection.add(ids=[mem_id], documents=[content], metadatas=[meta])
        return mem_id

    def search(self, query: str, n_results: int = 5) -> list:
        self._ensure_init()
        if not self._collection:
            return []
        try:
            results = self._collection.query(query_texts=[query], n_results=n_results)
        except Exception:
            return []

        memories = []
        if results and results["ids"] and results["ids"][0]:
            for i, mem_id in enumerate(results["ids"][0]):
                dist = results["distances"][0][i] if results.get("distances") else 0
                memories.append({
                    "id": mem_id,
                    "content": results["documents"][0][i],
                    "tags": results["metadatas"][0][i].get("tags", "").split(","),
                    "timestamp": results["metadatas"][0][i].get("timestamp", ""),
                    "relevance": round(1 - dist, 3)
                })
        return memories

    def get_all(self, limit: int = 100) -> list:
        self._ensure_init()
        try:
            results = self._collection.get(limit=limit)
        except Exception:
            return []

        memories = []
        if results and results["ids"]:
            for i, mem_id in enumerate(results["ids"]):
                memories.append({
                    "id": mem_id,
                    "content": results["documents"][i],
                    "tags": results["metadatas"][i].get("tags", "").split(","),
                    "timestamp": results["metadatas"][i].get("timestamp", "")
                })
        return memories

    def delete(self, mem_id: str):
        self._ensure_init()
        self._collection.delete(ids=[mem_id])

    def count(self) -> int:
        self._ensure_init()
        return self._collection.count()


memory_store = MemoryStore()
