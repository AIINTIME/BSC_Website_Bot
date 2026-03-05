from app.services.faq_loader import load_faqs
from app.services.embedding_service import create_embedding
from app.services.pinecone_service import upsert_vector
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

FAQ_NAMESPACE = settings.FAQ_NAMESPACE


def canonical_text(faq: dict) -> str:
    """Build a rich canonical string for embedding from a FAQ item."""
    parts = []
    if faq.get("category"):
        parts.append(f"Category: {faq['category']}")
    if faq.get("question"):
        parts.append(f"Question: {faq['question']}")
    if faq.get("answer"):
        parts.append(f"Answer: {faq['answer']}")
    if faq.get("keywords"):
        kws = faq["keywords"]
        if isinstance(kws, list):
            parts.append(f"Keywords: {', '.join(str(k) for k in kws)}")
    return "\n".join(parts)


def main():
    logger.info("Starting FAQ ingestion...")
    logger.info("FAQ_JSON_PATH: %s", settings.FAQ_JSON_PATH)
    logger.info("FAQ_NAMESPACE: %s", FAQ_NAMESPACE)

    faqs = load_faqs(settings.FAQ_JSON_PATH)

    if not isinstance(faqs, list):
        logger.error("load_faqs did not return a list. Got: %s", type(faqs))
        raise SystemExit(1)

    if not faqs:
        logger.error("No FAQs extracted from JSON. Check the FAQ_JSON_PATH and JSON structure.")
        raise SystemExit(1)

    logger.info("Loaded %d FAQs. Starting embedding and upsert...", len(faqs))

    success_count = 0
    error_count = 0

    for faq in faqs:
        faq_id = str(faq.get("id", ""))
        if not faq_id:
            logger.warning("Skipping FAQ with missing id: %s", faq)
            continue

        try:
            text = canonical_text(faq)
            embedding = create_embedding(text)

            upsert_vector(
                id=faq_id,
                vector=embedding,
                metadata={
                    "id": faq_id,
                    "category": faq.get("category", ""),
                    "question": faq.get("question", ""),
                    "answer": faq.get("answer", ""),
                    "keywords": faq.get("keywords", []),
                    "source": faq.get("source", "faq_json"),
                },
                namespace=FAQ_NAMESPACE
            )
            success_count += 1
            logger.info("[%d/%d] Upserted FAQ: %s", success_count, len(faqs), faq_id)

        except Exception as e:
            error_count += 1
            logger.error("Failed to upsert FAQ %s: %s", faq_id, str(e))

    logger.info("FAQ ingestion complete. Success: %d | Errors: %d", success_count, error_count)


if __name__ == "__main__":
    main()