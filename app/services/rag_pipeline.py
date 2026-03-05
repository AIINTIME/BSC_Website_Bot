# Context Database
import re
from app.core.config import settings
from app.services.retrieval_service import retrieve_candidates
from app.services.rerank_service import rerank
from app.services.rag_service import generate_answer
from app.services.memory_store_redis import append_turn

def _get_md(m):
    return m["metadata"] if isinstance(m, dict) else m.metadata

def _get_score(m):
    return m["score"] if isinstance(m, dict) else m.score


# ── Intent patterns ──────────────────────────────────────────────────────────
_GREETING_PATTERNS = re.compile(
    r"^\s*(hi+|hey+|hello+|good\s*(morning|afternoon|evening|day)|howdy|greetings|salam|salaam|assalamu\s*alaikum|what'?s\s*up|sup)\W*$",
    re.IGNORECASE
)
_THANKS_PATTERNS = re.compile(
    r"^\s*(thanks?|thank\s+you|thx|ty|appreciate\s*(it|that)?|great\s*thanks?|many\s+thanks)\W*$",
    re.IGNORECASE
)
_BYE_PATTERNS = re.compile(
    r"^\s*(bye+|goodbye|see\s+you|take\s+care|later|ciao|good\s*night|ok\s*bye|okay\s*bye)\W*$",
    re.IGNORECASE
)

_GREETING_RESPONSE = (
    "Hello! Welcome to **Bashundhara Sports City (BSC)** — Bangladesh's premier sports and fitness destination.\n\n"
    "I'm your virtual assistant and I'm here to help you with:\n"
    "• Membership plans & pricing\n"
    "• Facilities (cricket, football, swimming, gym, badminton, tennis & more)\n"
    "• Academy programs for all age groups\n"
    "• Event bookings & schedules\n"
    "• Opening hours & contact information\n\n"
    "How can I assist you today?"
)

_THANKS_RESPONSE = (
    "You're very welcome! 😊 If you have any more questions about Bashundhara Sports City — "
    "membership plans, facilities, academies, or bookings — feel free to ask anytime. "
    "We're happy to help!"
)

_BYE_RESPONSE = (
    "Thank you for visiting Bashundhara Sports City! We hope to welcome you soon. "
    "Feel free to return anytime if you have more questions. Have a wonderful day! 🏆"
)


def _detect_intent(query: str) -> str | None:
    """Returns 'greeting', 'thanks', 'bye', or None for regular queries."""
    q = query.strip()
    if _GREETING_PATTERNS.match(q):
        return "greeting"
    if _THANKS_PATTERNS.match(q):
        return "thanks"
    if _BYE_PATTERNS.match(q):
        return "bye"
    return None


def run_rag(user_query: str, session_id: str | None = None):
    # ── Short-circuit for greetings / thanks / bye ───────────────────────────
    intent = _detect_intent(user_query)
    if intent == "greeting":
        response_text = _GREETING_RESPONSE
    elif intent == "thanks":
        response_text = _THANKS_RESPONSE
    elif intent == "bye":
        response_text = _BYE_RESPONSE
    else:
        response_text = None

    if response_text is not None:
        result = {
            "answer": response_text,
            "confidence": 1.0,
            "rewritten_query": user_query,
            "sources": [],
            "rerank_reason": f"intent_{intent}"
        }
        if session_id:
            append_turn(session_id, user_query, response_text)
        return result

    # ── Standard RAG pipeline ────────────────────────────────────────────────
    # Pass session_id to retrieval (for contextual rewrite)
    candidates, top_score, rewritten = retrieve_candidates(user_query, session_id)

    print("\n[RAG PIPELINE DEBUG]")
    print("User query:", user_query)
    print("Rewritten query:", rewritten)
    print("Top retrieval score:", top_score)

    if candidates:
        md0 = _get_md(candidates[0])
        print("Top candidate metadata.id:", md0.get("id"))

    if not candidates:
        result = {
            "answer": (
                "I'm sorry, I don't have specific information on that right now. "
                "For accurate details, please contact our team:\n"
                "• Website: www.bashundharasportscity.com.bd\n"
                "• Email: info@bashundharasportscity.com.bd\n"
                "• We're open 5 AM – Midnight, every day of the year."
            ),
            "confidence": 0.0,
            "rewritten_query": rewritten,
            "sources": [],
            "rerank_reason": "no_candidates"
        }

        # Save memory even for fallback
        if session_id:
            append_turn(session_id, user_query, result["answer"])

        return result

    selected_ids, rerank_reason = rerank(
        user_query=user_query,
        matches=candidates,
        top_n=settings.RERANK_TOP_N
    )

    print("RERANK selected_ids:", selected_ids)
    print("RERANK reason:", rerank_reason)

    # Map IDs to matches
    by_id = {}
    for m in candidates:
        md = _get_md(m)
        mid = str(md.get("id", "")).strip()
        if mid:
            by_id[mid] = m

    selected = []
    for rid in selected_ids:
        rid = str(rid).strip()
        if rid in by_id:
            selected.append(by_id[rid])

    if not selected:
        result = {
            "answer": (
                "I'm sorry, I don't have specific information on that right now. "
                "For accurate details, please contact our team:\n"
                "• Website: www.bashundharasportscity.com.bd\n"
                "• Email: info@bashundharasportscity.com.bd\n"
                "• We're open 5 AM – Midnight, every day of the year."
            ),
            "confidence": float(top_score),
            "rewritten_query": rewritten,
            "sources": [],
            "rerank_reason": rerank_reason
        }

        if session_id:
            append_turn(session_id, user_query, result["answer"])

        return result

    # Generate grounded answer
    answer = generate_answer(user_query, selected)

    sources = [{
        "id": _get_md(m).get("id"),
        "question": _get_md(m).get("question"),
        "category": _get_md(m).get("category"),
        "score": float(_get_score(m))
    } for m in selected]

    result = {
        "answer": answer,
        "confidence": float(top_score),
        "rewritten_query": rewritten,
        "sources": sources,
        "rerank_reason": rerank_reason
    }

    # ✅ Save conversation turn into Redis
    if session_id:
        append_turn(session_id, user_query, answer)

    return result