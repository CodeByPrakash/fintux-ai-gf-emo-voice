import json
import uuid
import time
import asyncio
import aiosqlite
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH
from core.neural_engine import NeuralEngine
from core.affect import affect_model

router = APIRouter()

# Will be set from main.py
_engine: NeuralEngine = None


def set_engine(engine: NeuralEngine):
    global _engine
    _engine = engine


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket):
    await websocket.accept()
    session_id = str(uuid.uuid4())

    # Record session
    async with aiosqlite.connect(str(DB_PATH)) as db:
        await db.execute("INSERT INTO sessions (id) VALUES (?)", (session_id,))
        await db.commit()

    msg_count = 0
    last_activity = time.time()
    proactive_cooldown_until = time.time() + 35.0  # 35s initial grace period
    auto_proactive_enabled = True
    idle_threshold = 75.0  # seconds of silence before FENRY sends a casual check-in

    async def send_ws(msg_type: str, data: dict):
        try:
            await websocket.send_json({"type": msg_type, "data": data})
        except Exception:
            pass

    async def on_thinking_step(step: dict):
        await send_ws("thinking", step)

    async def send_proactive_message(reason: str = "idle"):
        nonlocal msg_count, last_activity
        if not _engine:
            return
        await send_ws("typing", {"active": True})
        try:
            starter_text = await _engine.generate_proactive_starter()
            if not starter_text:
                await send_ws("typing", {"active": False})
                return

            msg_count += 1
            await send_ws("message_complete", {
                "content": starter_text,
                "response_time_ms": 0,
                "is_proactive": True,
                "reason": reason
            })
            await send_ws("typing", {"active": False})
            await send_ws("affect", affect_model.get_state())

            # Persist FENRY's spontaneous message
            async with aiosqlite.connect(str(DB_PATH)) as db:
                await db.execute(
                    "INSERT INTO messages (session_id, role, content, response_time_ms) VALUES (?, ?, ?, ?)",
                    (session_id, "fenry", starter_text, 0)
                )
                await db.execute(
                    "UPDATE sessions SET message_count = ? WHERE id = ?",
                    (msg_count, session_id)
                )
                await db.commit()

            # Record in context window
            from core.context_window import context_manager
            await context_manager.add_message("assistant", starter_text, session_id)
            last_activity = time.time()
        except Exception as e:
            print(f"[PROACTIVE] Check-in error: {e}")
            await send_ws("typing", {"active": False})

    async def proactive_monitor():
        nonlocal last_activity, proactive_cooldown_until, auto_proactive_enabled
        while True:
            await asyncio.sleep(5)
            now = time.time()
            if auto_proactive_enabled and (now - last_activity >= idle_threshold) and (now >= proactive_cooldown_until):
                try:
                    async with aiosqlite.connect(str(DB_PATH)) as db:
                        async with db.execute("SELECT role FROM messages ORDER BY id DESC LIMIT 1") as cursor:
                            row = await cursor.fetchone()
                            # If FENRY spoke last, wait 3 minutes before another spontaneous check-in
                            if row and row[0] == "fenry":
                                proactive_cooldown_until = now + 180.0
                                continue
                except Exception:
                    pass

                await send_proactive_message("idle_checkin")
                proactive_cooldown_until = now + 240.0  # 4 min cooldown

    proactive_task = asyncio.create_task(proactive_monitor())

    try:
        # Send initial status
        await send_ws("status", {"connected": True, "session_id": session_id})
        await send_ws("affect", affect_model.get_state())

        while True:
            raw = await websocket.receive_text()
            last_activity = time.time()
            try:
                incoming = json.loads(raw)
            except (json.JSONDecodeError, AttributeError):
                incoming = {"content": raw}

            # Handle control events
            if incoming.get("type") == "trigger_proactive":
                await send_proactive_message("user_nudge")
                continue
            elif incoming.get("type") == "set_auto_proactive":
                auto_proactive_enabled = bool(incoming.get("enabled", True))
                continue

            user_message = incoming.get("content", incoming.get("message", raw))
            if not user_message or not str(user_message).strip():
                continue

            msg_count += 1
            start = time.time()

            # Send typing indicator
            await send_ws("typing", {"active": True})

            # Store user message
            async with aiosqlite.connect(str(DB_PATH)) as db:
                await db.execute(
                    "INSERT INTO messages (session_id, role, content) VALUES (?, ?, ?)",
                    (session_id, "user", user_message)
                )
                await db.commit()

            # Stream response
            full_response = []
            async for chunk in _engine.think(user_message, session_id=session_id, on_step=on_thinking_step):
                full_response.append(chunk)
                await send_ws("message_chunk", {"content": chunk})

            response_text = "".join(full_response)
            elapsed_ms = round((time.time() - start) * 1000)

            # Send complete message
            await send_ws("message_complete", {
                "content": response_text,
                "response_time_ms": elapsed_ms
            })
            await send_ws("typing", {"active": False})
            await send_ws("affect", affect_model.get_state())

            # Store FENRY response
            async with aiosqlite.connect(str(DB_PATH)) as db:
                await db.execute(
                    "INSERT INTO messages (session_id, role, content, response_time_ms) VALUES (?, ?, ?, ?)",
                    (session_id, "fenry", response_text, elapsed_ms)
                )
                await db.execute(
                    "INSERT INTO mood_history (mood, energy, attachment) VALUES (?, ?, ?)",
                    (affect_model.mood, affect_model.energy, affect_model.attachment)
                )
                await db.execute(
                    "UPDATE sessions SET message_count = ? WHERE id = ?",
                    (msg_count, session_id)
                )
                await db.commit()

    except WebSocketDisconnect:
        proactive_task.cancel()
        async with aiosqlite.connect(str(DB_PATH)) as db:
            await db.execute(
                "UPDATE sessions SET end_time = CURRENT_TIMESTAMP WHERE id = ?",
                (session_id,)
            )
            await db.commit()
    except Exception as e:
        proactive_task.cancel()
        print(f"[WS] Error: {e}")
        try:
            await send_ws("error", {"message": str(e)})
        except Exception:
            pass


@router.post("/api/chat/proactive")
async def trigger_proactive_checkin():
    """Manual or scheduled REST trigger to generate a proactive check-in message."""
    if not _engine:
        return {"error": "Neural engine not loaded"}
    starter = await _engine.generate_proactive_starter()
    return {"starter": starter}


@router.get("/api/chat/history")
async def get_chat_history(limit: int = 50):
    """Retrieve persistent conversation history from SQLite."""
    async with aiosqlite.connect(str(DB_PATH)) as db:
        async with db.execute(
            """
            SELECT id, role, content, timestamp, response_time_ms
            FROM messages
            ORDER BY id DESC LIMIT ?
            """,
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            messages = []
            for r in reversed(rows):
                messages.append({
                    "id": r[0],
                    "role": r[1],
                    "content": r[2],
                    "timestamp": r[3],
                    "response_time_ms": r[4]
                })
            return {"messages": messages}


@router.get("/api/chat/context")
async def get_context_state():
    """Retrieve current context window stats, rolling summary, and personalization profile."""
    from core.context_window import context_manager
    await context_manager.initialize()
    return {
        "recent_messages_count": len(context_manager.history),
        "rolling_summary": context_manager.rolling_summary,
        "user_profile": context_manager.user_profile,
        "max_recent_messages": context_manager.max_recent_messages,
    }
