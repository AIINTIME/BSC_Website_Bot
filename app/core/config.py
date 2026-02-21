import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
    LLM_MODEL = os.getenv("LLM_MODEL")
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", 0.78))
    TOP_K = int(os.getenv("TOP_K", 5))
    RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", 4))
    UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")
    REDIS_TTL_SECONDS = int(os.getenv("REDIS_TTL_SECONDS", 1800))
    REDIS_MAX_MESSAGES = int(os.getenv("REDIS_MAX_MESSAGES", 10))

settings = Settings()