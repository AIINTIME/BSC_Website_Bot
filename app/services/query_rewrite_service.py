# from openai import OpenAI
# from app.core.config import settings

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# SYSTEM_REWRITE = """
# Rewrite the user question into a neutral, information-seeking search query for FAQ retrieval.

# Rules:
# - Remove tone, negativity, sarcasm, persuasion.
# - Preserve key entities and topics (HIT, Haldia, admission, fee, hostel, placements, NAAC, NBA, etc.).
# - If user asks yes/no, rewrite into "information about <topic>".
# - Output ONLY the rewritten query. No quotes, no extra text.
# """.strip()

# def rewrite_for_retrieval(user_query: str) -> str:
#     resp = client.chat.completions.create(
#         model=settings.LLM_MODEL,
#         messages=[
#             {"role": "system", "content": SYSTEM_REWRITE},
#             {"role": "user", "content": user_query},
#         ],
#         temperature=0
#     )
#     return resp.choices[0].message.content.strip()

# Rewrite
# from openai import OpenAI
# from app.core.config import settings

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# SYSTEM_REWRITE = """
# Rewrite the user question into a neutral, information-seeking search query for FAQ retrieval.

# Rules:
# - Remove tone, negativity, sarcasm, persuasion.
# - Preserve key entities and topics (HIT, Haldia, admission, fee, hostel, placements, NAAC, NBA, etc.).
# - If user asks yes/no, rewrite into "information about <topic>".
# - Output ONLY the rewritten query. No quotes, no extra text.
# """.strip()

# def rewrite_for_retrieval(user_query: str) -> str:
#     resp = client.chat.completions.create(
#         model=settings.LLM_MODEL,
#         messages=[
#             {"role": "system", "content": SYSTEM_REWRITE},
#             {"role": "user", "content": user_query},
#         ],
#         temperature=0
#     )
#     return resp.choices[0].message.content.strip()

# Context_Database
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_REWRITE_CTX = """
Rewrite the user's message into a neutral search query for FAQ retrieval.

You are given recent conversation history.
Rules:
- Resolve pronouns like "it", "there", "that" using the history.
- Remove tone/sarcasm/negativity; keep factual intent.
- Preserve entities and topics (HIT, admission, fees, hostel, placements).
- Output ONLY the rewritten query string.
""".strip()

def rewrite_for_retrieval(user_query: str, history: list[dict]) -> str:
    # keep it short to reduce tokens
    context = history[-6:] if history else []
    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_REWRITE_CTX},
            {"role": "user", "content": f"HISTORY:\n{context}\n\nUSER:\n{user_query}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()