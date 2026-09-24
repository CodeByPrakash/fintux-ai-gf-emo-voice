import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PERSONA_DIR

router = APIRouter(prefix="/api/persona", tags=["persona"])

PERSONA_FILE = PERSONA_DIR / "gf_model.yaml"


def _load_persona() -> dict:
    try:
        with open(PERSONA_FILE, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return {"name": "FENRY", "style": {"tone": "gentle, playful"}, "affection_level": 0.8}


def _save_persona(data: dict):
    PERSONA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PERSONA_FILE, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


@router.get("")
async def get_persona():
    return _load_persona()


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    tone: Optional[str] = None
    address_user: Optional[List[str]] = None
    emoji: Optional[bool] = None
    interests: Optional[List[str]] = None
    affection_level: Optional[float] = None


@router.put("")
async def update_persona(update: PersonaUpdate):
    persona = _load_persona()
    data = update.model_dump(exclude_none=True)

    if "tone" in data or "address_user" in data or "emoji" in data:
        style = persona.get("style", {})
        if "tone" in data:
            style["tone"] = data.pop("tone")
        if "address_user" in data:
            style["address_user"] = data.pop("address_user")
        if "emoji" in data:
            style["emoji"] = data.pop("emoji")
        persona["style"] = style

    persona.update(data)
    _save_persona(persona)
    return persona


@router.post("/reset")
async def reset_persona():
    default = {
        "name": "FENRY",
        "role": "companion",
        "personality": "caring",
        "style": {
            "tone": "gentle, playful, encouraging, goal-focused",
            "address_user": ["baby", "love", "darling"],
            "emoji": True
        },
        "interests": ["python", "anime", "AI", "gym", "music"],
        "guidelines": {"respectful": True, "supportive": True, "encouraging": True},
        "affection_level": 0.8,
        "learning": {"memorize_preferences": True, "suggest_habits": True,
                      "celebrate_milestones": True}
    }
    _save_persona(default)
    return default
