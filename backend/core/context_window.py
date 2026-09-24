import json
import asyncio
import aiosqlite
from typing import List, Dict, Any, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH


class ContextWindowManager:
    """
    Intelligent Context Window & Personalization Manager for FENRY-GF.
    - Manages recent conversation window with token estimation
    - Maintains rolling conversational summaries for infinite long-term memory
    - Loads & persists chat history across server restarts & sessions
    - Manages a persistent personalization profile (preferences, nicknames, facts)
    """

    def __init__(self, max_recent_messages: int = 14, max_tokens: int = 4000):
        self.db_path = str(DB_PATH)
        self.max_recent_messages = max_recent_messages
        self.max_tokens = max_tokens
        self.history: List[Dict[str, str]] = []
        self.rolling_summary: str = ""
        self.user_profile: Dict[str, str] = {}
        self._initialized = False

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation: 1 token ~= 4 characters."""
        return max(1, len(text) // 4)

    async def initialize(self):
        """Load persistent history, latest rolling summary, and user profile."""
        if self._initialized:
            return

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Load user profile
            async with db.execute("SELECT key, value FROM user_profile") as cursor:
                async for row in cursor:
                    self.user_profile[row[0]] = row[1]

            # 2. Load latest rolling summary
            async with db.execute(
                "SELECT summary FROM conversation_summaries ORDER BY id DESC LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    self.rolling_summary = row[0]

            # 3. Load recent chat history
            loaded = []
            async with db.execute(
                """
                SELECT role, content FROM messages
                ORDER BY id DESC LIMIT ?
                """,
                (self.max_recent_messages * 2,)
            ) as cursor:
                async for row in cursor:
                    role = "assistant" if row[0] in ("fenry", "assistant") else "user"
                    loaded.append({"role": role, "content": row[1]})

            # Restore in chronological order
            self.history = list(reversed(loaded))

        self._initialized = True

    async def add_message(self, role: str, content: str, session_id: str = None, llm_client=None):
        """Append message and trigger compaction / summary if context window exceeds budget."""
        await self.initialize()

        norm_role = "assistant" if role in ("fenry", "assistant") else "user"
        self.history.append({"role": norm_role, "content": content})

        # If history exceeds max recent turns, trigger background rolling summary
        if len(self.history) > self.max_recent_messages * 2:
            overflow_turns = self.history[:-self.max_recent_messages]
            self.history = self.history[-self.max_recent_messages:]

            if llm_client:
                asyncio.create_task(self._summarize_overflow(overflow_turns, session_id, llm_client))

    async def _summarize_overflow(self, turns: List[Dict[str, str]], session_id: str, llm_client):
        """Summarizes older conversation turns into rolling summary without blocking."""
        try:
            conversation_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in turns])
            prompt = (
                "You are an assistant memory engine. Summarize the following dialogue into 2-3 concise sentences "
                "capturing key topics discussed, the user's emotional state, preferences, and important context.\n\n"
                f"Existing Summary so far: {self.rolling_summary or 'None'}\n\n"
                f"New Dialogue to merge:\n{conversation_text}\n\n"
                "Updated Cumulative Summary:"
            )
            new_summary = await llm_client.generate_oneshot(prompt)
            if new_summary and len(new_summary.strip()) > 10:
                self.rolling_summary = new_summary.strip()
                async with aiosqlite.connect(self.db_path) as db:
                    await db.execute(
                        "INSERT INTO conversation_summaries (session_id, summary) VALUES (?, ?)",
                        (session_id or "default", self.rolling_summary)
                    )
                    await db.commit()
        except Exception:
            pass

    async def set_profile_field(self, key: str, value: str, category: str = "general"):
        self.user_profile[key] = value
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO user_profile (key, value, category, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP
                """,
                (key, value, category)
            )
            await db.commit()

    async def get_profile(self) -> Dict[str, str]:
        await self.initialize()
        return dict(self.user_profile)

    def build_context_messages(
        self,
        system_prompt: str,
        user_message: str,
        graph_context: str = "",
        vector_context: str = "",
        tool_context: str = ""
    ) -> List[Dict[str, str]]:
        """
        Constructs the optimized, token-budgeted prompt payload for the LLM.
        Integrates:
        1. Enhanced System Prompt with Persona & Guidelines
        2. Personalization Profile (user traits, preferences)
        3. Rolling Long-term Context Summary
        4. Structured Knowledge Graph Subgraph (Node & Edge relations)
        5. Semantic Vector Memories
        6. Sliding window of recent turns
        """
        context_blocks = []

        if self.user_profile:
            profile_lines = ["USER PERSONAL PROFILE:"]
            for k, v in self.user_profile.items():
                profile_lines.append(f"- {k}: {v}")
            context_blocks.append("\n".join(profile_lines))

        if self.rolling_summary:
            context_blocks.append(f"PREVIOUS CONVERSATION RECAP:\n{self.rolling_summary}")

        if graph_context:
            context_blocks.append(graph_context)

        if vector_context:
            context_blocks.append(f"RELEVANT VECTOR MEMORIES:\n{vector_context}")

        if tool_context:
            context_blocks.append(f"[REAL-TIME TOOL RESULTS]:\n{tool_context}")

        full_system = system_prompt
        if context_blocks:
            full_system += "\n\n" + "\n\n".join(context_blocks)

        messages = [{"role": "system", "content": full_system}]

        # Include recent history from sliding window
        recent_history = self.history[-self.max_recent_messages:]
        for msg in recent_history:
            messages.append(msg)

        # Append current user prompt
        messages.append({"role": "user", "content": user_message})
        return messages


context_manager = ContextWindowManager()
