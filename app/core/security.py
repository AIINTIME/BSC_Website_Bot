"""
Optional API-key security for BSC Website Bot.
When BOT_API_KEY is set in .env, all protected endpoints require the
header:  X-API-Key: <value>

If BOT_API_KEY is not set, the dependency passes through (dev-friendly).
"""
from fastapi import Header, HTTPException, status
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """
    FastAPI dependency: validates X-API-Key header when BOT_API_KEY is configured.
    Usage:
        @router.get("/secure", dependencies=[Depends(verify_api_key)])
    """
    expected = settings.BOT_API_KEY
    if not expected:
        # No key configured — open access (suitable for local dev)
        return

    if x_api_key != expected:
        logger.warning("Unauthorized access attempt with key: %s", x_api_key)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header."
        )
