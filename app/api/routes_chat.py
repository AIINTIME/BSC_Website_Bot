import asyncio
import json
import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.chat_models import ChatRequest, ChatResponse
from app.services.rag_pipeline import run_rag
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# ── Short-circuit patterns (mirrored from rag_pipeline) ───────────────────────
_GREETING_RE = re.compile(
    r"^\s*(hi+|hey+|hello+|good\s*(morning|afternoon|evening|day)|howdy|greetings|"
    r"salam|salaam|assalamu\s*alaikum|what'?s\s*up|sup)\W*$", re.IGNORECASE
)
_THANKS_RE = re.compile(
    r"^\s*(thanks?|thank\s+you|thx|ty|appreciate\s*(it|that)?|great\s*thanks?|many\s+thanks)\W*$",
    re.IGNORECASE
)
_BYE_RE = re.compile(
    r"^\s*(bye+|goodbye|see\s+you|take\s+care|later|ciao|good\s*night|ok\s*bye|okay\s*bye)\W*$",
    re.IGNORECASE
)
_STATIC = {
    "greeting": (
        "Hello! Welcome to **Bashundhara Sports City (BSC)** — Bangladesh's premier sports "
        "and fitness destination.\n\n"
        "I'm here to help you with:\n"
        "• Membership plans & pricing\n"
        "• Facilities (cricket, football, swimming, gym, badminton, tennis & more)\n"
        "• Academy programs for all age groups\n"
        "• Event bookings & schedules\n"
        "• Opening hours & contact information\n\n"
        "How can I assist you today?"
    ),
    "thanks": (
        "You're very welcome! If you have any more questions about Bashundhara Sports City — "
        "membership plans, facilities, academies, or bookings — feel free to ask anytime."
    ),
    "bye": (
        "Thank you for visiting Bashundhara Sports City! We hope to welcome you soon. "
        "Feel free to return anytime if you have more questions. Have a wonderful day!"
    ),
}


def _detect_static(q: str) -> str | None:
    if _GREETING_RE.match(q): return "greeting"
    if _THANKS_RE.match(q):   return "thanks"
    if _BYE_RE.match(q):      return "bye"
    return None


# ── Standard (non-streaming) endpoint ────────────────────────────────────────
@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    Standard chat endpoint with full response.
    Kept for backwards compatibility and fallback.
    """
    try:
        result = run_rag(req.message, session_id=req.session_id)
        return result
    except Exception as e:
        logger.error("Chat endpoint error: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# ── Streaming endpoint ────────────────────────────────────────────────────────
@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    Streaming SSE endpoint — returns answer tokens as they arrive.
    First token in ~1.5-2s. Eliminates the separate rerank call.

    SSE event format:
      data: {"token": "..."}       — one or more answer tokens
      data: {"done": true, "sources": [...]}  — final event
      data: {"error": "..."}       — on failure
    """
    async def generate():
        try:
            q = req.message.strip()

            # ── Instant responses for greetings / thanks / bye ───────────────
            intent = _detect_static(q)
            if intent:
                text = _STATIC[intent]
                yield f"data: {json.dumps({'token': text})}\n\n"
                yield f"data: {json.dumps({'done': True, 'sources': []})}\n\n"
                if req.session_id:
                    await asyncio.to_thread(_save_turn, req.session_id, q, text)
                return

            # ── Retrieval runs in a thread (sync libs: Redis, Pinecone) ──────
            matches, top_score, rewritten = await asyncio.to_thread(
                _retrieve, q, req.session_id
            )
            logger.debug("Stream retrieval | score=%.3f rewritten=%s", top_score, rewritten[:60])

            # ── Source metadata for final event ──────────────────────────────
            sources = [
                {
                    "id":       (m["metadata"] if isinstance(m, dict) else m.metadata).get("id"),
                    "question": (m["metadata"] if isinstance(m, dict) else m.metadata).get("question"),
                    "category": (m["metadata"] if isinstance(m, dict) else m.metadata).get("category"),
                    "score":    float(m["score"] if isinstance(m, dict) else m.score),
                }
                for m in matches[:4]
            ]

            # ── Stream answer (rerank + generate merged into one GPT call) ───
            from app.services.stream_service import stream_rag_answer
            full_answer = ""
            async for token in stream_rag_answer(rewritten, matches):
                full_answer += token
                yield f"data: {json.dumps({'token': token})}\n\n"

            yield f"data: {json.dumps({'done': True, 'sources': sources})}\n\n"

            # ── Persist conversation turn ─────────────────────────────────────
            if req.session_id and full_answer:
                await asyncio.to_thread(_save_turn, req.session_id, q, full_answer)

        except Exception as e:
            logger.error("Stream error: %s", str(e), exc_info=True)
            yield f"data: {json.dumps({'error': 'An error occurred. Please try again.'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


# ── Sync helpers (called via asyncio.to_thread) ────────────────────────────────
def _retrieve(message: str, session_id: str | None):
    from app.services.retrieval_service import retrieve_candidates
    return retrieve_candidates(message, session_id)


def _save_turn(session_id: str, user_msg: str, bot_msg: str):
    from app.services.memory_store_redis import append_turn
    append_turn(session_id, user_msg, bot_msg)
