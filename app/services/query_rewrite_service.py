import re
from openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Pronouns that require conversation context to resolve
_NEEDS_CONTEXT = re.compile(
    r'\b(it|its|they|them|their|that|this|those|these|there|he|she|him|her|one|do so)\b',
    re.IGNORECASE
)

SYSTEM_REWRITE_CTX = """
Rewrite the user's message into a clear, neutral search query for FAQ retrieval about Bashundhara Sports City (BSC).

You are given recent conversation history.
Rules:
- If the message is a greeting, farewell, thank-you, or any non-informational social phrase (e.g. "hi", "thanks", "bye"), return it EXACTLY as-is — do NOT expand it.
- Resolve pronouns like "it", "there", "that", "they" using the conversation history.
- Remove emotional tone, sarcasm, or negativity — keep factual intent only.
- Preserve key entities: BSC, membership plans (Silver/Gold/Platinum/Corporate), facilities (cricket, football, swimming pool, gym, badminton, basketball, tennis, indoor arena), academies (cricket, football, swimming, martial arts, badminton, tennis), events, booking, contact, fees, schedule, opening hours.
- Do NOT add information the user did not mention. Only expand/clarify what is genuinely ambiguous.
- Output ONLY the rewritten query string — no explanation, no punctuation other than the query itself.
""".strip()


def rewrite_for_retrieval(user_query: str, history: list[dict]) -> str:
    """
    Returns a rewritten query optimised for vector search.
    Skips the GPT call entirely when:
      - There is no conversation history, OR
      - The query contains no context-dependent pronouns.
    This alone saves ~1.5s on the majority of queries.
    """
    context = history[-4:] if history else []   # trimmed to 4 (was 6)

    # ── Fast path: no rewrite needed ────────────────────────────────────────
    if not context or not _NEEDS_CONTEXT.search(user_query):
        logger.debug("Rewrite skipped (no context dependency): %s", user_query)
        return user_query

    # ── Slow path: resolve pronouns via GPT ─────────────────────────────────
    logger.debug("Rewriting query with context | history_len=%d", len(context))
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_REWRITE_CTX},
            {"role": "user", "content": f"HISTORY:\n{context}\n\nUSER:\n{user_query}"}
        ],
        temperature=0,
        max_tokens=80,      # rewritten query is always short
    )
    return resp.choices[0].message.content.strip()