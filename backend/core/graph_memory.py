import re
import json
import uuid
import asyncio
import aiosqlite
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class GraphMemory:
    """
    Persistent Knowledge Graph Memory System for FENRY-GF.
    Represents memories as connected Entity Nodes and Semantic Edges.
    Enables multi-hop associative recall and deep personalization.
    """

    def __init__(self):
        self.db_path = str(DB_PATH)

    async def _init_root_nodes(self):
        """Ensure standard anchor nodes exist."""
        await self.get_or_create_node("User", "PERSON", {"description": "The user chatting with FENRY"})
        await self.get_or_create_node("FENRY", "AI_COMPANION", {"description": "FENRY, the caring AI girlfriend"})

    async def get_or_create_node(self, label: str, entity_type: str = "ENTITY", properties: dict = None) -> str:
        clean_label = label.strip()
        node_id = clean_label.lower().replace(" ", "_")
        props_json = json.dumps(properties or {})

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, properties FROM graph_nodes WHERE id = ?", (node_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    # Update properties and timestamp
                    existing_props = json.loads(row[1] or "{}")
                    if properties:
                        existing_props.update(properties)
                    await db.execute(
                        "UPDATE graph_nodes SET properties = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (json.dumps(existing_props), node_id)
                    )
                    await db.commit()
                    return node_id

            await db.execute(
                """
                INSERT INTO graph_nodes (id, label, entity_type, properties)
                VALUES (?, ?, ?, ?)
                """,
                (node_id, clean_label, entity_type, props_json)
            )
            await db.commit()
        return node_id

    async def add_edge(
        self,
        source_label: str,
        target_label: str,
        relation: str,
        weight: float = 1.0,
        context: str = "",
        source_type: str = "ENTITY",
        target_type: str = "ENTITY"
    ) -> str:
        source_id = await self.get_or_create_node(source_label, source_type)
        target_id = await self.get_or_create_node(target_label, target_type)
        clean_rel = relation.strip().upper().replace(" ", "_")
        edge_id = f"{source_id}__{clean_rel}__{target_id}"

        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT id, weight FROM graph_edges WHERE id = ?", (edge_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    new_weight = min(5.0, (row[1] or 1.0) + 0.2)
                    await db.execute(
                        """
                        UPDATE graph_edges
                        SET weight = ?, context = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (new_weight, context[:500] if context else "", edge_id)
                    )
                    await db.commit()
                    return edge_id

            await db.execute(
                """
                INSERT INTO graph_edges (id, source_id, target_id, relation, weight, context)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (edge_id, source_id, target_id, clean_rel, weight, context[:500] if context else "")
            )
            await db.commit()
        return edge_id

    async def get_node_edges(self, node_id: str) -> List[Dict[str, Any]]:
        """Retrieve outgoing and incoming relations for a given node."""
        results = []
        async with aiosqlite.connect(self.db_path) as db:
            # Outgoing
            async with db.execute(
                """
                SELECT e.id, e.relation, e.weight, e.context, n.id, n.label, n.entity_type
                FROM graph_edges e
                JOIN graph_nodes n ON e.target_id = n.id
                WHERE e.source_id = ?
                ORDER BY e.weight DESC
                """,
                (node_id,)
            ) as cursor:
                async for row in cursor:
                    results.append({
                        "direction": "out",
                        "relation": row[1],
                        "weight": row[2],
                        "context": row[3],
                        "target_id": row[4],
                        "target_label": row[5],
                        "target_type": row[6]
                    })

            # Incoming
            async with db.execute(
                """
                SELECT e.id, e.relation, e.weight, e.context, n.id, n.label, n.entity_type
                FROM graph_edges e
                JOIN graph_nodes n ON e.source_id = n.id
                WHERE e.target_id = ?
                ORDER BY e.weight DESC
                """,
                (node_id,)
            ) as cursor:
                async for row in cursor:
                    results.append({
                        "direction": "in",
                        "relation": row[1],
                        "weight": row[2],
                        "context": row[3],
                        "source_id": row[4],
                        "source_label": row[5],
                        "source_type": row[6]
                    })
        return results

    async def find_relevant_subgraph(self, query: str, max_facts: int = 8) -> List[Dict[str, Any]]:
        """
        Finds nodes matching words in query, traverses 1-2 hops,
        and returns human-readable relationship facts.
        """
        tokens = [t.lower() for t in re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", query)]
        # Filter common stopwords
        stopwords = {"the", "and", "that", "this", "with", "have", "from", "what", "where", "when", "your", "about", "feel", "will"}
        meaningful_tokens = [t for t in tokens if t not in stopwords]

        facts = []
        visited_edges = set()

        async with aiosqlite.connect(self.db_path) as db:
            # First, fetch direct User facts (always high relevance for personalization)
            async with db.execute(
                """
                SELECT e.id, s.label, e.relation, t.label, e.weight, e.context
                FROM graph_edges e
                JOIN graph_nodes s ON e.source_id = s.id
                JOIN graph_nodes t ON e.target_id = t.id
                WHERE e.source_id = 'user'
                ORDER BY e.weight DESC, e.updated_at DESC
                LIMIT ?
                """,
                (max_facts,)
            ) as cursor:
                async for row in cursor:
                    edge_id, s_lbl, rel, t_lbl, wt, ctx = row
                    visited_edges.add(edge_id)
                    # Check if matching query tokens
                    is_match = any(t in t_lbl.lower() or t in rel.lower() or t in (ctx or "").lower() for t in meaningful_tokens)
                    facts.append({
                        "source": s_lbl,
                        "relation": rel,
                        "target": t_lbl,
                        "context": ctx,
                        "priority": 2 if is_match else 1
                    })

            # Next, search for nodes matching query tokens
            matched_node_ids = set()
            for token in meaningful_tokens[:5]:
                async with db.execute(
                    "SELECT id FROM graph_nodes WHERE id LIKE ? OR label LIKE ? LIMIT 5",
                    (f"%{token}%", f"%{token}%")
                ) as cursor:
                    async for r in cursor:
                        matched_node_ids.add(r[0])

            # Retrieve edges for matched nodes
            for n_id in matched_node_ids:
                async with db.execute(
                    """
                    SELECT e.id, s.label, e.relation, t.label, e.weight, e.context
                    FROM graph_edges e
                    JOIN graph_nodes s ON e.source_id = s.id
                    JOIN graph_nodes t ON e.target_id = t.id
                    WHERE (e.source_id = ? OR e.target_id = ?)
                    ORDER BY e.weight DESC
                    LIMIT 5
                    """,
                    (n_id, n_id)
                ) as cursor:
                    async for row in cursor:
                        edge_id, s_lbl, rel, t_lbl, wt, ctx = row
                        if edge_id not in visited_edges:
                            visited_edges.add(edge_id)
                            facts.append({
                                "source": s_lbl,
                                "relation": rel,
                                "target": t_lbl,
                                "context": ctx,
                                "priority": 3
                            })

        # Sort facts by priority
        facts.sort(key=lambda x: x["priority"], reverse=True)
        return facts[:max_facts]

    async def get_graph_context_prompt(self, user_message: str) -> str:
        """Generates a structured knowledge graph memory block for LLM prompt."""
        subgraph = await self.find_relevant_subgraph(user_message, max_facts=7)
        if not subgraph:
            return ""

        lines = ["KNOWLEDGE GRAPH MEMORY (Personal Facts & Connected Concepts):"]
        for f in subgraph:
            detail = f" [Context: {f['context']}]" if f.get("context") else ""
            lines.append(f"- ({f['source']}) -[{f['relation']}]-> ({f['target']}){detail}")
        return "\n".join(lines)

    async def extract_from_interaction(self, user_message: str, fenry_reply: str, llm_client=None):
        """
        Extracts new entities, preferences, emotions, and relations from conversation.
        Uses fast heuristic extraction + LLM extraction for deep semantic nodes.
        """
        await self._init_root_nodes()
        text = user_message.strip()
        lower = text.lower()

        # 1. Heuristic pattern extraction for instant updates
        # Likes
        likes_patterns = [
            r"i (?:really )?(?:love|like|enjoy|adore)\s+([a-zA-Z0-9\s_]{2,30})",
            r"my favorite\s+([a-zA-Z0-9\s_]{2,20})\s+is\s+([a-zA-Z0-9\s_]{2,30})"
        ]
        for p in likes_patterns:
            m = re.search(p, lower)
            if m:
                target = m.group(1).strip()
                if target and len(target) < 35:
                    await self.add_edge("User", target.title(), "LIKES", 1.5, f"User said: {text}", target_type="PREFERENCE")

        # Dislikes
        dislikes_match = re.search(r"i (?:hate|dislike|can't stand|despise)\s+([a-zA-Z0-9\s_]{2,30})", lower)
        if dislikes_match:
            target = dislikes_match.group(1).strip()
            if target:
                await self.add_edge("User", target.title(), "DISLIKES", 1.5, f"User said: {text}", target_type="PREFERENCE")

        # Working on / Projects / Tasks
        work_match = re.search(r"i(?:'m| am) (?:working on|building|coding|studying|preparing for)\s+([a-zA-Z0-9\s_]{2,35})", lower)
        if work_match:
            project = work_match.group(1).strip()
            if project:
                await self.add_edge("User", project.title(), "WORKING_ON", 1.5, f"User said: {text}", target_type="PROJECT")

        # Emotions / State
        feel_match = re.search(r"i(?:'m| am) (?:feeling\s+)?(tired|stressed|happy|sad|excited|anxious|bored|lonely|sleepy|depressed|overwhelmed|great|good|fine|exhausted)", lower)
        if feel_match:
            emotion = feel_match.group(1).strip()
            await self.add_edge("User", emotion.title(), "CURRENT_MOOD", 1.2, f"User said: {text}", target_type="EMOTION")

        # Goals / Plans
        goal_match = re.search(r"my goal is to\s+([a-zA-Z0-9\s_]{3,40})|i want to\s+([a-zA-Z0-9\s_]{3,40})", lower)
        if goal_match:
            goal = (goal_match.group(1) or goal_match.group(2) or "").strip()
            if goal and len(goal.split()) >= 2:
                await self.add_edge("User", goal.capitalize(), "GOAL_IS", 1.5, f"User said: {text}", target_type="GOAL")

        # Pets / Relationships
        pet_match = re.search(r"my (?:cat|dog|pet)(?:'s)? name is\s+([a-zA-Z]{2,20})|i have a (?:dog|cat|pet) named\s+([a-zA-Z]{2,20})", lower)
        if pet_match:
            pet_name = (pet_match.group(1) or pet_match.group(2) or "").strip()
            if pet_name:
                await self.add_edge("User", pet_name.title(), "HAS_PET", 2.0, f"User said: {text}", target_type="PERSON")

        # 2. LLM-assisted knowledge graph extraction for complex context (when message is rich)
        if llm_client and len(text.split()) >= 6:
            asyncio.create_task(self._async_llm_extract(text, llm_client))

    async def _async_llm_extract(self, text: str, llm_client):
        """Asynchronously calls LLM to extract entity-relationship triples."""
        try:
            prompt = (
                "Extract structured facts about the USER from this statement as JSON array.\n"
                f'Statement: "{text}"\n'
                "Output strictly a JSON list of objects with keys: source (usually 'User'), target, relation, type.\n"
                "Example: [{\"source\": \"User\", \"target\": \"Python\", \"relation\": \"PROGRAMS_IN\", \"type\": \"SKILL\"}]\n"
                "If no meaningful personal facts, output []. Only JSON, no markdown:"
            )
            raw = await llm_client.generate_oneshot(prompt)
            clean = raw.strip().strip("`").replace("json\n", "").strip()
            start_idx = clean.find("[")
            end_idx = clean.rfind("]")
            if start_idx != -1 and end_idx != -1:
                items = json.loads(clean[start_idx:end_idx + 1])
                for item in items:
                    target = str(item.get("target", "")).strip()
                    relation = str(item.get("relation", "")).strip()
                    entity_type = str(item.get("type", "ENTITY")).strip()
                    if target and relation and len(target) < 40:
                        await self.add_edge("User", target.title(), relation, 1.0, text, target_type=entity_type)
        except Exception as e:
            # Silent fallback so extraction never breaks app
            pass

    async def get_all_nodes(self, limit: int = 100) -> List[Dict[str, Any]]:
        nodes = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT id, label, entity_type, properties, updated_at FROM graph_nodes ORDER BY updated_at DESC LIMIT ?",
                (limit,)
            ) as cursor:
                async for row in cursor:
                    nodes.append({
                        "id": row[0],
                        "label": row[1],
                        "entity_type": row[2],
                        "properties": json.loads(row[3] or "{}"),
                        "updated_at": row[4]
                    })
        return nodes

    async def get_all_edges(self, limit: int = 150) -> List[Dict[str, Any]]:
        edges = []
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT id, source_id, target_id, relation, weight, context, updated_at
                FROM graph_edges
                ORDER BY weight DESC, updated_at DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                async for row in cursor:
                    edges.append({
                        "id": row[0],
                        "source": row[1],
                        "target": row[2],
                        "relation": row[3],
                        "weight": row[4],
                        "context": row[5],
                        "updated_at": row[6]
                    })
        return edges

    async def get_graph_export(self) -> Dict[str, Any]:
        """Returns the full network graph structure for visualization."""
        nodes = await self.get_all_nodes(limit=80)
        edges = await self.get_all_edges(limit=120)
        return {"nodes": nodes, "edges": edges}

    async def delete_node(self, node_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM graph_edges WHERE source_id = ? OR target_id = ?", (node_id, node_id))
            await db.execute("DELETE FROM graph_nodes WHERE id = ?", (node_id,))
            await db.commit()


graph_memory = GraphMemory()
