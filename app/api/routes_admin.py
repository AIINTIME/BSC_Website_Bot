"""
Admin endpoints for BSC Website Bot.
Protected by X-API-Key header when BOT_API_KEY is set in .env.
"""
from fastapi import APIRouter, Depends
from app.core.security import verify_api_key
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", dependencies=[Depends(verify_api_key)])
def admin_health():
    """
    System health check.
    Pings Redis and checks Pinecone index availability.
    """
    from app.services.memory_store_redis import redis_client
    from app.services.pinecone_service import index

    health = {
        "status": "ok",
        "bot": "BSC Website Bot",
        "redis": "unknown",
        "pinecone": "unknown",
    }

    # Redis ping
    try:
        redis_client.ping()
        health["redis"] = "ok"
    except Exception as e:
        health["redis"] = f"error: {str(e)}"
        health["status"] = "degraded"

    # Pinecone check
    try:
        stats = index.describe_index_stats()
        total_vectors = stats.get("total_vector_count", 0) if isinstance(stats, dict) else getattr(stats, "total_vector_count", 0)
        health["pinecone"] = f"ok (vectors: {total_vectors})"
    except Exception as e:
        health["pinecone"] = f"error: {str(e)}"
        health["status"] = "degraded"

    return health


@router.get("/index-stats", dependencies=[Depends(verify_api_key)])
def admin_index_stats():
    """
    Returns detailed Pinecone index statistics including per-namespace vector counts.
    """
    from app.services.pinecone_service import index

    try:
        stats = index.describe_index_stats()
        if hasattr(stats, "__dict__"):
            stats = stats.__dict__
        return {"index_name": settings.PINECONE_INDEX_NAME, "stats": stats}
    except Exception as e:
        logger.error("Failed to fetch index stats: %s", str(e))
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Failed to fetch index stats: {str(e)}")
