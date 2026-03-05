import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")

    # Pinecone
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX_NAME: str = os.getenv("PINECONE_INDEX_NAME", "bsc-website-bot")
    PINECONE_ENVIRONMENT: str = os.getenv("PINECONE_ENVIRONMENT", "us-east-1")

    # Knowledge base / FAQ
    FAQ_JSON_PATH: str = os.getenv("FAQ_JSON_PATH", "data/bashundhara-sports-city-content.json")
    FAQ_NAMESPACE: str = os.getenv("FAQ_NAMESPACE", "bsc_v1")

    # Retrieval & Reranking
    SIMILARITY_THRESHOLD: float = float(os.getenv("SIMILARITY_THRESHOLD", 0.70))
    TOP_K: int = int(os.getenv("TOP_K", 20))
    RERANK_TOP_N: int = int(os.getenv("RERANK_TOP_N", 4))

    # Redis session memory
    UPSTASH_REDIS_URL: str = os.getenv("UPSTASH_REDIS_URL", "")
    REDIS_TTL_SECONDS: int = int(os.getenv("REDIS_TTL_SECONDS", 1800))
    REDIS_MAX_MESSAGES: int = int(os.getenv("REDIS_MAX_MESSAGES", 10))
    REDIS_KEY_PREFIX: str = os.getenv("REDIS_KEY_PREFIX", "bscbot")

    # Security (optional — leave unset for open dev access)
    BOT_API_KEY: str | None = os.getenv("BOT_API_KEY") or None

    # CORS — comma-separated list of allowed origins
    ALLOWED_ORIGINS: list[str] = [
        o.strip()
        for o in os.getenv(
            "ALLOWED_ORIGINS",
            "https://bashundharasportscity.com.bd,https://www.bashundharasportscity.com.bd,http://localhost:8000,http://localhost:3000"
        ).split(",")
        if o.strip()
    ]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", 20))


settings = Settings()