# from app.services.faq_loader import load_faqs
# from app.services.embedding_service import create_embedding
# from app.services.pinecone_service import upsert_vector

# def canonical_text(faq):
#     return f"""
#     Category: {faq['category']}
#     Question: {faq['question']}
#     Answer: {faq['answer']}
#     Tags: {", ".join(faq.get("tags", []))}
#     """

# faqs = load_faqs()

# for faq in faqs:
#     text = canonical_text(faq)
#     embedding = create_embedding(text)
#     upsert_vector(
#         id=str(faq["id"]),
#         vector=embedding,
#         metadata={
#             "question": faq["question"],
#             "answer": faq["answer"],
#             "category": faq["category"]
#         }
#     )

# print("FAQ ingestion complete.")

# Reqwrite
from app.services.faq_loader import load_faqs
from app.services.embedding_service import create_embedding
from app.services.pinecone_service import upsert_vector

FAQ_NAMESPACE = "faq_v2"

faqs = load_faqs("data/hit_faq_rag.json")

print("Loaded FAQs:", len(faqs))
print("First FAQ id:", faqs[0].get("id"))

for faq in faqs:
    text = faq.get("chunk_text") or f"Q: {faq.get('question','')}\nA: {faq.get('answer','')}"
    embedding = create_embedding(text)

    upsert_vector(
        id=str(faq["id"]),  # Pinecone vector ID
        vector=embedding,
        metadata={
            "id": str(faq["id"]),                # ✅ REQUIRED for rerank mapping
            "q_no": faq.get("q_no"),
            "question": faq.get("question", ""),
            "answer": faq.get("answer", ""),
            "category": faq.get("category", ""),
            "keywords": faq.get("keywords", []),
            "source": faq.get("source", "")
        },
        namespace=FAQ_NAMESPACE
    )

print("FAQ ingestion complete.")