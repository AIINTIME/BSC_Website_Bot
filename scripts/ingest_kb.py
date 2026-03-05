import json
from app.core.config import settings
from app.services.embedding_service import create_embedding
from app.services.pinecone_service import upsert_vector
from app.services.website_kb_builder import build_documents
from app.utils.chunking import chunk_text
from app.core.logging import get_logger

logger = get_logger(__name__)


def main():
    logger.info("Starting KB ingestion...")
    logger.info("FAQ_JSON_PATH: %s", settings.FAQ_JSON_PATH)
    logger.info("FAQ_NAMESPACE: %s", settings.FAQ_NAMESPACE)

    with open(settings.FAQ_JSON_PATH, "r", encoding="utf-8") as f:
        site_json = json.load(f)

    # Build logical documents from the whole website JSON
    docs = build_documents(site_json, client=settings.REDIS_KEY_PREFIX)
    logger.info("Built %d documents from website JSON", len(docs))

    total_chunks = 0
    error_count = 0

    for doc_idx, doc in enumerate(docs, start=1):
        base_text = doc.get("chunk_text") or doc.get("answer") or ""
        chunks = chunk_text(base_text, max_chars=1200, overlap=200)

        for i, ch in enumerate(chunks, start=1):
            chunk_id = f"{doc['id']}_CH_{i}"
            try:
                emb = create_embedding(ch)

                upsert_vector(
                    id=chunk_id,
                    vector=emb,
                    metadata={
                        "id": chunk_id,
                        "doc_id": doc["id"],
                        "client": settings.REDIS_KEY_PREFIX,
                        "category": doc.get("category", ""),
                        "path_group": doc.get("path_group", ""),
                        "source": doc.get("source", "website_json"),
                        # question/answer for reranker and grounded answering
                        "question": doc.get("question", f"Website content for {doc.get('category', '')}"),
                        "answer": ch,  # use the chunk text as the answer body
                        "text": ch,     # alias for rag_service compatibility
                    },
                    namespace=settings.FAQ_NAMESPACE
                )
                total_chunks += 1

                if total_chunks % 10 == 0:
                    logger.info("Progress: %d chunks upserted (doc %d/%d)", total_chunks, doc_idx, len(docs))

            except Exception as e:
                error_count += 1
                logger.error("Failed to upsert chunk %s: %s", chunk_id, str(e))

    logger.info("KB ingestion complete. Total chunks: %d | Errors: %d", total_chunks, error_count)


if __name__ == "__main__":
    main()