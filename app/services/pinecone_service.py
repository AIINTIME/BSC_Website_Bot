from pinecone import Pinecone
from app.core.config import settings

pc = Pinecone(api_key=settings.PINECONE_API_KEY)
index = pc.Index(settings.PINECONE_INDEX_NAME)

def upsert_vector(id: str, vector: list, metadata: dict, namespace: str = "default"):
    index.upsert(
        vectors=[{"id": id, "values": vector, "metadata": metadata}],
        namespace=namespace
    )

def query_vector(vector: list, top_k: int, namespace: str = "default"):
    return index.query(
        vector=vector,
        top_k=top_k,
        include_metadata=True,
        namespace=namespace
    )