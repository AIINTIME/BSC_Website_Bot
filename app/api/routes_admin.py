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


@router.get("/test-sheets")
def test_sheets():
    """Quick Google Sheets connectivity test — no auth required."""
    result = {"step": "", "error": None, "ok": False}
    try:
        import json
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        result["step"] = "import_ok"

        if settings.GOOGLE_SERVICE_ACCOUNT_FILE:
            creds = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"],
            )
            import json as _json
            with open(settings.GOOGLE_SERVICE_ACCOUNT_FILE) as f:
                result["service_account"] = _json.load(f).get("client_email", "unknown")
        else:
            info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_JSON)
            result["service_account"] = info.get("client_email", "unknown")
            creds = service_account.Credentials.from_service_account_info(
                info,
                scopes=["https://www.googleapis.com/auth/spreadsheets",
                        "https://www.googleapis.com/auth/drive"],
            )
        svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
        result["step"] = "service_built"

        meta = svc.spreadsheets().get(spreadsheetId=settings.GOOGLE_SPREADSHEET_ID).execute()
        result["spreadsheet"] = meta["properties"]["title"]
        result["step"] = "spreadsheet_read"

        svc.spreadsheets().values().append(
            spreadsheetId=settings.GOOGLE_SPREADSHEET_ID,
            range="Contacts_1!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": [["TEST_ROW", "test@bsc.com", "01700000000", "Dhaka", "admin-test"]]},
        ).execute()
        result["step"] = "row_written"
        result["ok"] = True
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {e}"
    return result


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
