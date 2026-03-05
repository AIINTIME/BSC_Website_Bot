# Context Database
from app.core.config import settings
from app.services.retrieval_service import retrieve_candidates
from app.services.rerank_service import rerank
from app.services.rag_service import generate_answer
from app.services.memory_store_redis import append_turn

def _get_md(m):
    return m["metadata"] if isinstance(m, dict) else m.metadata

def _get_score(m):
    return m["score"] if isinstance(m, dict) else m.score


def run_rag(user_query: str, session_id: str | None = None):
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
            "answer": "Great question! For the most accurate answer, our team at Bashundhara Sports City would love to help you personally. Visit us at www.bashundharasportscity.com.bd, email info@bashundharasportscity.com.bd, or drop by our reception — we're open 5 AM to Midnight, 365 days a year!",
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
            "answer": "Great question! For the most accurate answer, our team at Bashundhara Sports City would love to help you personally. Visit us at www.bashundharasportscity.com.bd, email info@bashundharasportscity.com.bd, or drop by our reception — we're open 5 AM to Midnight, 365 days a year!",
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