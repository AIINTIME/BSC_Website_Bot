from fastapi import APIRouter, HTTPException
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.rag_pipeline import run_rag
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Main chat endpoint.
    Accepts a user message and optional session_id for conversational memory.
    Memory is persisted in Redis via run_rag() → append_turn().
    """
    try:
        result = run_rag(req.message, session_id=req.session_id)
        return result
    except Exception as e:
        logger.error("Chat endpoint error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")
