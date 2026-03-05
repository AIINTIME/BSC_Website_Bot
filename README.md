# BSC Website Bot

**AI-powered FAQ & information assistant for [Bashundhara Sports City](https://www.bashundharasportscity.com.bd)** — Bangladesh's premier sports and fitness complex.

Built with **FastAPI + OpenAI + Pinecone + Redis** using a full RAG pipeline: query rewriting → vector retrieval → LLM reranking → grounded answer generation → session memory.

---

## 🏗️ Architecture

```
User Query
    │
    ├── Query Rewrite (GPT-4o-mini)       → resolves pronouns using Redis session history
    │
    ├── Embedding (text-embedding-3-small) → dense vector
    │
    ├── Pinecone Retrieval (top_k=20)     → cosine similarity search (namespace: bsc_v1)
    │
    ├── LLM Rerank (GPT-4o-mini)          → selects top_n=4 most relevant docs
    │
    ├── Grounded Generation (GPT-4o-mini) → answer from context only
    │
    └── Redis Memory (Upstash)            → stores session history (TTL: 30 min)
```

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | ✅ | Your OpenAI API key |
| `PINECONE_API_KEY` | ✅ | Your Pinecone API key |
| `PINECONE_INDEX_NAME` | ✅ | Pinecone index name (e.g. `bsc-website-bot`) |
| `PINECONE_ENVIRONMENT` | ✅ | Pinecone region (e.g. `us-east-1`) |
| `UPSTASH_REDIS_URL` | ✅ | Upstash Redis connection URL (`rediss://...`) |
| `EMBEDDING_MODEL` | ✅ | e.g. `text-embedding-3-small` |
| `LLM_MODEL` | ✅ | e.g. `gpt-4o-mini` |
| `FAQ_JSON_PATH` | ✅ | Path to website JSON (e.g. `data/bashundhara-sports-city-content.json`) |
| `FAQ_NAMESPACE` | ✅ | Pinecone namespace (e.g. `bsc_v1`) |
| `SIMILARITY_THRESHOLD` | Optional | Default `0.70` |
| `TOP_K` | Optional | Retrieval candidates, default `20` |
| `RERANK_TOP_N` | Optional | Final docs after rerank, default `4` |
| `REDIS_TTL_SECONDS` | Optional | Session TTL, default `1800` (30 min) |
| `REDIS_MAX_MESSAGES` | Optional | Messages kept in session, default `10` |
| `BOT_API_KEY` | Optional | Secret key for admin endpoint protection |
| `ALLOWED_ORIGINS` | Optional | Comma-separated CORS origins |

---

## 📦 Installation

```bash
git clone <repo-url>
cd Development

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate       # Windows
# source .venv/bin/activate  # Linux/macOS

pip install -r requirements.txt
```

---

## 🗄️ Data Ingestion

Run **once** (or after updating the website JSON) to populate Pinecone:

```bash
# Ingest full website KB (chunked documents)
python -m scripts.ingest_kb

# Ingest explicit FAQ items (membership FAQs, facility info, academy programs)
python -m scripts.ingest_faqs

# Check index stats
python -m scripts.check_index
```

---

## 🚀 Running the Server

```bash
uvicorn app.main:app --reload --port 8000
```

- Interactive API docs: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/](http://localhost:8000/)

---

## 📡 API Endpoints

### `POST /api/chat`
Main chat endpoint. Answers questions about BSC using RAG.

**Request:**
```json
{
  "message": "What are the membership plans?",
  "session_id": "user-abc-123"
}
```

**Response:**
```json
{
  "answer": "Bashundhara Sports City offers four membership tiers...",
  "confidence": 0.87,
  "rewritten_query": "membership plans Bashundhara Sports City",
  "sources": [
    {"id": "BSC_PLAN_2", "question": "Gold membership", "category": "Membership Plans", "score": 0.87}
  ],
  "rerank_reason": "Direct answer to membership pricing query"
}
```

### `GET /api/admin/health`
Returns Redis and Pinecone connectivity status. Requires `X-API-Key` header if `BOT_API_KEY` is set.

### `GET /api/admin/index-stats`
Returns detailed Pinecone namespace vector counts. Requires `X-API-Key` header.

---

## 🗂️ Project Structure

```
Development/
├── app/
│   ├── api/
│   │   ├── routes_chat.py       # POST /api/chat
│   │   └── routes_admin.py      # GET /api/admin/*
│   ├── core/
│   │   ├── config.py            # Settings from .env
│   │   ├── logging.py           # Structured logging
│   │   └── security.py          # API key auth dependency
│   ├── models/
│   │   ├── chat_models.py       # ChatRequest / ChatResponse
│   │   └── faq_models.py        # FAQItem
│   ├── services/
│   │   ├── rag_pipeline.py      # Orchestrates the RAG flow
│   │   ├── rag_service.py       # LLM answer generation
│   │   ├── retrieval_service.py # Embedding + Pinecone query
│   │   ├── rerank_service.py    # LLM reranking
│   │   ├── embedding_service.py # OpenAI embeddings
│   │   ├── pinecone_service.py  # Pinecone upsert/query
│   │   ├── memory_store_redis.py# Session history in Redis
│   │   ├── query_rewrite_service.py # Pronoun resolution
│   │   ├── faq_loader.py        # JSON → FAQ items
│   │   └── website_kb_builder.py# JSON → KB documents
│   ├── utils/
│   │   ├── chunking.py          # Text chunking with overlap
│   │   ├── confidence.py        # Score → label helper
│   │   └── text_utils.py        # Normalization helpers
│   └── main.py                  # FastAPI app entry point
├── data/
│   └── bashundhara-sports-city-content.json
├── scripts/
│   ├── ingest_kb.py             # Ingest website KB chunks
│   ├── ingest_faqs.py           # Ingest FAQ items
│   └── check_index.py           # Inspect Pinecone index
├── .env                         # Environment configuration
├── requirements.txt             # Pinned dependencies
└── README.md
```