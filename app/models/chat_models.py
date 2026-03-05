from pydantic import BaseModel, Field
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User's question or message")
    session_id: Optional[str] = Field(default=None, description="Session ID for conversational memory")


class SourceItem(BaseModel):
    id: Optional[str] = None
    question: Optional[str] = None
    category: Optional[str] = None
    score: Optional[float] = None


class ChatResponse(BaseModel):
    answer: str
    confidence: float
    rewritten_query: Optional[str] = None
    sources: List[SourceItem] = []
    rerank_reason: Optional[str] = None
