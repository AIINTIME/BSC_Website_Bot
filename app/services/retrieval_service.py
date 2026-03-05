from app.services.embedding_service import create_embedding
from app.services.pinecone_service import query_vector
from app.core.config import settings
from app.services.query_rewrite_service import rewrite_for_retrieval
from app.services.memory_store_redis import get_history

FAQ_NAMESPACE = settings.FAQ_NAMESPACE

def retrieve_candidates(user_query: str, session_id: str | None = None):
    history = get_history(session_id) if session_id else []
    rewritten = rewrite_for_retrieval(user_query, history)

    emb = create_embedding(rewritten)

    results = query_vector(emb, settings.TOP_K, namespace=FAQ_NAMESPACE)
    matches = results["matches"] if isinstance(results, dict) else results.matches

    if not matches:
        return [], 0.0, rewritten

    top_score = matches[0]["score"] if isinstance(matches[0], dict) else matches[0].score
    return matches, float(top_score), rewritten