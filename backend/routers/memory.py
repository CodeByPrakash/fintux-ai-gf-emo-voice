from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.memory_store import memory_store
from core.graph_memory import graph_memory

router = APIRouter(prefix="/api/memories", tags=["memory"])


@router.get("")
async def list_memories(limit: int = 100):
    return memory_store.get_all(limit=limit)


@router.get("/search")
async def search_memories(q: str, n: int = 5):
    return memory_store.search(q, n_results=n)


@router.delete("/{mem_id}")
async def delete_memory(mem_id: str):
    memory_store.delete(mem_id)
    return {"deleted": mem_id}


@router.get("/count")
async def memory_count():
    nodes = await graph_memory.get_all_nodes(limit=1000)
    return {
        "vector_count": memory_store.count(),
        "graph_node_count": len(nodes),
        "count": memory_store.count() + len(nodes)
    }


# Knowledge Graph Endpoints
@router.get("/graph")
async def get_knowledge_graph():
    """Returns nodes and edges for graph visualization and memory inspection."""
    return await graph_memory.get_graph_export()


class GraphEdgeCreate(BaseModel):
    source: str
    target: str
    relation: str
    weight: Optional[float] = 1.0
    context: Optional[str] = ""
    source_type: Optional[str] = "ENTITY"
    target_type: Optional[str] = "ENTITY"


@router.post("/graph/edge")
async def add_graph_edge(edge: GraphEdgeCreate):
    edge_id = await graph_memory.add_edge(
        source_label=edge.source,
        target_label=edge.target,
        relation=edge.relation,
        weight=edge.weight or 1.0,
        context=edge.context or "",
        source_type=edge.source_type or "ENTITY",
        target_type=edge.target_type or "ENTITY"
    )
    return {"status": "ok", "edge_id": edge_id}


@router.delete("/graph/node/{node_id}")
async def delete_graph_node(node_id: str):
    await graph_memory.delete_node(node_id)
    return {"status": "ok", "deleted_node": node_id}


@router.get("/graph/subgraph")
async def query_subgraph(query: str):
    subgraph = await graph_memory.find_relevant_subgraph(query, max_facts=10)
    return {"query": query, "facts": subgraph}
