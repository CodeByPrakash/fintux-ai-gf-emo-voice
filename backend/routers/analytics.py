import aiosqlite
from fastapi import APIRouter
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_PATH
from core.affect import affect_model
from core.memory_store import memory_store

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def get_overview():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        db.row_factory = aiosqlite.Row

        cur = await db.execute("SELECT COUNT(*) as c FROM messages")
        row = await cur.fetchone()
        total_messages = row[0] if row else 0

        cur = await db.execute("SELECT COUNT(*) as c FROM sessions")
        row = await cur.fetchone()
        total_sessions = row[0] if row else 0

        cur = await db.execute(
            "SELECT AVG(response_time_ms) as avg_rt FROM messages WHERE role='fenry' AND response_time_ms IS NOT NULL"
        )
        row = await cur.fetchone()
        avg_rt = round(row[0], 1) if row and row[0] else 0

    return {
        "total_messages": total_messages,
        "total_sessions": total_sessions,
        "avg_response_time_ms": avg_rt,
        "memories_stored": memory_store.count(),
        "current_affect": affect_model.get_state()
    }


@router.get("/mood-history")
async def get_mood_history(limit: int = 50):
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cur = await db.execute(
            "SELECT mood, energy, attachment, timestamp FROM mood_history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cur.fetchall()
    return [{"mood": r[0], "energy": r[1], "attachment": r[2], "timestamp": r[3]} for r in reversed(rows)]


@router.get("/activity")
async def get_activity():
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cur = await db.execute(
            """SELECT strftime('%H', timestamp) as hour, COUNT(*) as cnt
               FROM messages GROUP BY hour ORDER BY hour"""
        )
        rows = await cur.fetchall()
    return [{"hour": int(r[0]) if r[0] else 0, "count": r[1]} for r in rows]


@router.get("/messages")
async def get_messages(limit: int = 50):
    async with aiosqlite.connect(str(DB_PATH)) as db:
        cur = await db.execute(
            "SELECT role, content, response_time_ms, timestamp FROM messages ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = await cur.fetchall()
    return [{"role": r[0], "content": r[1], "response_time_ms": r[2], "timestamp": r[3]} for r in reversed(rows)]
