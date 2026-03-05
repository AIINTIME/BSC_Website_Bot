from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_chat import router as chat_router
from app.api.routes_admin import router as admin_router
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="BSC Website Bot",
    description="AI-powered assistant for Bashundhara Sports City — answers questions about facilities, membership, academies, events, and more.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(admin_router, prefix="/api/admin", tags=["Admin"])


# ── Startup checks ────────────────────────────────────────────────────────────
@app.on_event("startup")
async def startup_checks():
    logger.info("BSC Website Bot starting up...")

    # Redis connectivity check
    try:
        from app.services.memory_store_redis import redis_client
        redis_client.ping()
        logger.info("Redis connection: OK")
    except Exception as e:
        logger.warning("Redis connection failed at startup: %s", str(e))

    # Pinecone connectivity check
    try:
        from app.services.pinecone_service import index
        index.describe_index_stats()
        logger.info("Pinecone connection: OK (index: %s)", settings.PINECONE_INDEX_NAME)
    except Exception as e:
        logger.warning("Pinecone connection failed at startup: %s", str(e))

    logger.info("BSC Website Bot ready.")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def health():
    return {"status": "BSC Website Bot Running", "version": "1.0.0"}