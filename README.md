# HIT AI FAQ Bot

Enterprise-grade RAG chatbot for HIT Haldia website.

## 🚀 Architecture

- FastAPI Backend
- OpenAI (LLM + Embeddings)
- Pinecone (Vector DB)
- Upstash Redis (Session Memory)
- Query Rewrite + Rerank + Grounded Generation

## 🔧 Features

- Context-aware conversational memory
- Enterprise reranking
- Strict grounding to official FAQs
- Redis TTL session management
- Source citation
- Debug tracing

## 📦 Installation

```bash
git clone <repo-url>
cd HIT_Website_Bot
pip install -r requirements.txt