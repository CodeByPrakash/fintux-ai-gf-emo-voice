from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None
    thinking_steps: Optional[List[dict]] = None


class WSMessage(BaseModel):
    type: str  # message, thinking, typing, status, affect, error
    data: dict


class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    tone: Optional[str] = None
    address_user: Optional[List[str]] = None
    emoji: Optional[bool] = None
    interests: Optional[List[str]] = None
    affection_level: Optional[float] = None
    no_explicit: Optional[bool] = None
    consent_required: Optional[bool] = None


class AffectState(BaseModel):
    mood: float = 0.7
    energy: float = 0.8
    attachment: float = 0.5


class MemoryItem(BaseModel):
    id: str
    content: str
    tags: List[str] = []
    timestamp: str
    relevance: Optional[float] = None


class AnalyticsOverview(BaseModel):
    total_messages: int = 0
    total_sessions: int = 0
    avg_response_time_ms: float = 0
    memories_stored: int = 0
    current_affect: AffectState = Field(default_factory=AffectState)
