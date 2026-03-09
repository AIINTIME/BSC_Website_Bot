"""
Async streaming service — merges reranking + answer generation into ONE GPT call.
Previously: rerank call (~2-3s) + generate call (~3-4s) = ~5-7s
Now:        single streaming call, first token in ~0.5s after retrieval.
"""
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

# ── Combined system prompt ────────────────────────────────────────────────────
# Instructs GPT to: 1) internally pick the best docs, 2) answer from them.
# No separate rerank call needed — saves one full ~3s round-trip.
_SYSTEM = """
You are the official AI assistant for Bashundhara Sports City (BSC) — Bangladesh's premier sports and fitness complex.

You are given up to {n} context documents. Internally select the most relevant ones, then write your answer using ONLY those.

RULES:
1. Answer directly and confidently from the provided context.
2. For pricing: state exact figures (e.g. "Gold membership is BDT 4,500/month").
3. For facilities: reference international standards where available (FIFA, BWF, FIBA, Olympic).
4. For academies: mention professional coaching, program structure, and age groups.
5. If NO document is relevant: respond with exactly — "I'm sorry, I don't have specific information on that right now. For accurate details, please contact our team:\n• Website: www.bashundharasportscity.com.bd\n• Email: info@bashundharasportscity.com.bd\n• We're open 5 AM – Midnight, every day of the year."
6. NEVER invent prices, dates, or facts not in the provided documents.
7. Format: bullet points for lists. Keep responses concise (3–8 lines).
8. Refer to the facility as "Bashundhara Sports City" or "BSC".
9. End with a natural follow-up offer when appropriate.
""".strip()


def _build_context(matches: list) -> str:
    parts = []
    for i, m in enumerate(matches[:8]):
        md = m["metadata"] if isinstance(m, dict) else m.metadata
        parts.append(
            f"[DOC {i+1}] {md.get('category','')}\n"
            f"Q: {md.get('question','')}\n"
            f"A: {md.get('answer') or md.get('text','')}"
        )
    return "\n\n".join(parts)


async def stream_rag_answer(user_query: str, matches: list):
    """
    Async generator that yields answer tokens one by one.
    Merges rerank + generate into a single streaming OpenAI call.
    First token typically arrives in < 600ms after this is called.
    """
    if not matches:
        fallback = (
            "I'm sorry, I don't have specific information on that right now. "
            "For accurate details, please contact our team:\n"
            "• Website: www.bashundharasportscity.com.bd\n"
            "• Email: info@bashundharasportscity.com.bd\n"
            "• We're open 5 AM – Midnight, every day of the year."
        )
        yield fallback
        return

    context = _build_context(matches)
    n = min(len(matches), 8)

    logger.debug("Streaming answer | docs=%d query=%s", n, user_query[:60])

    stream = await _client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM.format(n=n)},
            {"role": "user",   "content": f"CONTEXT:\n{context}\n\nQUESTION:\n{user_query}"},
        ],
        temperature=0,
        max_tokens=450,
        stream=True,
    )

    async for chunk in stream:
        token = chunk.choices[0].delta.content or ""
        if token:
            yield token
