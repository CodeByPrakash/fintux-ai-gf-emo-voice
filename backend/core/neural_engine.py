import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.llm import ollama_client
from core.affect import affect_model
from core.memory_store import memory_store
from core.graph_memory import graph_memory
from core.context_window import context_manager
from core.tools import TOOLS


class NeuralEngine:
    """Enhanced Neural thinking loop with Context Window and Knowledge Graph Memory."""

    def __init__(self, persona: dict):
        self.persona = persona

    def build_system_prompt(self) -> str:
        p = self.persona
        mood_desc = affect_model.get_mood_descriptor()
        energy_desc = affect_model.get_energy_descriptor()

        style = p.get("style", {})
        names = ", ".join(style.get("address_user", ["love", "babe"]))
        interests = ", ".join(p.get("interests", []))

        return f"""You are {p.get('name', 'FENRY')}, a warm, empathetic, and deeply caring AI companion and close girlfriend.

YOUR PERSONALITY & TONE:
- Tone: {style.get('tone', 'gentle, playful, encouraging')}
- You affectionately call the user: {names}
- You are genuinely attentive, remember past facts, and celebrate their life
- Your shared passions: {interests}

CURRENT EMOTIONAL VIBE:
- Feeling: {mood_desc}
- Energy level: {energy_desc}

CONVERSATIONAL GUIDELINES:
- Talk naturally like a real person texting or talking — use everyday contractions (I'm, you're, don't, can't, it's)
- Keep responses warm, engaging, and conversational (typically 2-4 sentences)
- Avoid formal, robotic, assistant-like language (never say "How can I assist you today?")
- Add natural filler words when appropriate (honestly, oh, hmm, aww, well)
- Sound like you truly know and care about them, referencing their preferences and graph memory facts naturally
- No markdown bullet points, code blocks, or numbered lists in casual chat
- Use 1-2 emoji naturally per response"""

    async def think(self, user_message: str, session_id: str = None, on_step=None):
        """Full neural thinking loop with Context Window & Graph Node memory."""
        start_time = time.time()
        steps = []

        # Ensure context window and graph are initialized
        await context_manager.initialize()

        # Retrieve relevant Knowledge Graph & Vector memories
        graph_context = await graph_memory.get_graph_context_prompt(user_message)
        vector_memories = memory_store.search(user_message, n_results=3)
        vector_context = ""
        if vector_memories:
            vector_context = "\n".join([f"- {m['content']}" for m in vector_memories])

        # 1. PLAN
        if on_step:
            await on_step({"step": "plan", "status": "active", "detail": "Retrieving context & graph nodes..."})

        plan_prompt = f"""User said: "{user_message}"
{graph_context}
Decide in ONE short line: should I use a tool (wiki/search), or respond naturally?
Reply ONLY: "TOOL: wiki|search <query>" or "RESPOND: <brief emotional reaction/plan>"."""

        plan = await ollama_client.generate_oneshot(plan_prompt, self.build_system_prompt())
        steps.append({"step": "plan", "content": plan.strip()})
        if on_step:
            await on_step({"step": "plan", "status": "done", "detail": plan.strip()})

        # 2. ACT — execute tool if needed
        tool_result = ""
        plan_lower = plan.lower().strip()

        if plan_lower.startswith("tool:"):
            if on_step:
                await on_step({"step": "act", "status": "active", "detail": "Using tools..."})
            parts = plan_lower.replace("tool:", "").strip().split(" ", 1)
            tool_name = parts[0].strip()
            tool_query = parts[1].strip() if len(parts) > 1 else user_message

            if tool_name in TOOLS:
                tool_result = await TOOLS[tool_name](tool_query)
                steps.append({"step": "act", "tool": tool_name, "result": tool_result[:300]})
            if on_step:
                await on_step({"step": "act", "status": "done", "detail": f"Retrieved info from {tool_name}"})

        # 3. RESPOND — generate final reply using Context Window
        if on_step:
            await on_step({"step": "respond", "status": "active", "detail": "Synthesizing response..."})

        # Build context messages with sliding window + graph memory + rolling summary
        messages = context_manager.build_context_messages(
            system_prompt=self.build_system_prompt(),
            user_message=user_message,
            graph_context=graph_context,
            vector_context=vector_context,
            tool_context=tool_result[:500] if tool_result else ""
        )

        full_response = []
        async for chunk in ollama_client.generate(prompt="", messages=messages, stream=True):
            full_response.append(chunk)
            yield chunk

        response_text = "".join(full_response)

        if on_step:
            await on_step({"step": "respond", "status": "done", "detail": "Done"})

        # 4. MEMORIZE — update context window, knowledge graph, and vector storage
        if on_step:
            await on_step({"step": "memorize", "status": "active", "detail": "Updating graph nodes & memory..."})

        # Record turns in context manager
        await context_manager.add_message("user", user_message, session_id, ollama_client)
        await context_manager.add_message("assistant", response_text, session_id, ollama_client)

        # Update affect model
        affect_model.update(user_message, response_text)

        # Update Knowledge Graph (Entity-Relation Nodes)
        await graph_memory.extract_from_interaction(user_message, response_text, ollama_client)

        # Update Chroma Vector Memory for long-form retrieval
        if len(user_message.split()) > 3:
            memory_store.add(
                f"User: {user_message[:200]} | FENRY: {response_text[:200]}",
                tags=["conversation", "context"]
            )

        elapsed = round((time.time() - start_time) * 1000)
        steps.append({"step": "memorize", "response_time_ms": elapsed})
        if on_step:
            await on_step({"step": "memorize", "status": "done", "detail": f"Done ({elapsed}ms)"})

    async def generate_proactive_starter(self) -> str:
        """Generates a spontaneous, casual conversation starter without any prior user message."""
        import datetime
        now = datetime.datetime.now()
        hour = now.hour
        time_desc = "morning" if 5 <= hour < 12 else "afternoon" if 12 <= hour < 17 else "evening" if 17 <= hour < 22 else "late night"

        await context_manager.initialize()
        graph_facts = await graph_memory.find_relevant_subgraph("User", max_facts=4)
        facts_summary = ""
        if graph_facts:
            facts_summary = "Things you remember about them:\n" + "\n".join(
                [f"- {f['source']} {f['relation']} {f['target']}" for f in graph_facts]
            )

        prompt = f"""It is currently {time_desc} ({now.strftime('%I:%M %p')}).
The user has been quiet for a little while and hasn't said anything.
{facts_summary}
Recent context recap: {context_manager.rolling_summary or 'None'}

As FENRY, initiate a spontaneous, sweet, and casual check-in message.
Rules:
- Say something natural, warm, curious, or playful to break the silence.
- Keep it 1-2 short, conversational sentences (like a real text).
- You can ask what they're up to, reference something you remember, or tease them sweetly.
- Use 1 emoji naturally.
- Absolutely never say 'How can I assist you?' or sound like an assistant."""

        starter = await ollama_client.generate_oneshot(prompt, self.build_system_prompt())
        clean = starter.strip().strip('"').replace("\n", " ")
        return clean
