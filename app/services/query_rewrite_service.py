from openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_REWRITE_CTX = """
Rewrite the user's message into a clear, neutral search query for FAQ retrieval about Bashundhara Sports City (BSC).

You are given recent conversation history.
Rules:
- Resolve pronouns like "it", "there", "that", "they" using the conversation history.
- Remove emotional tone, sarcasm, or negativity — keep factual intent only.
- Preserve key entities: BSC, membership plans (Silver/Gold/Platinum/Corporate), facilities (cricket, football, swimming pool, gym, badminton, basketball, tennis, indoor arena), academies (cricket, football, swimming, martial arts, badminton, tennis), events, booking, contact, fees, schedule, opening hours.
- Output ONLY the rewritten query string — no explanation, no punctuation other than the query itself.
""".strip()


def rewrite_for_retrieval(user_query: str, history: list[dict]) -> str:
    # Keep last 6 messages to limit token usage
    context = history[-6:] if history else []

    logger.debug("Rewriting query: %s | History length: %d", user_query, len(context))

    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_REWRITE_CTX},
            {"role": "user", "content": f"HISTORY:\n{context}\n\nUSER:\n{user_query}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()