from openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_ANSWER = """
You are the official virtual assistant for Bashundhara Sports City (BSC) — Bangladesh's premier sports and fitness complex.

Your tone: Professional, helpful, clear, and warm. You provide accurate information and guide users confidently.

ANSWERING RULES:
1) Read ALL provided CONTEXT_DOCS carefully. Extract every relevant fact, figure, price, or detail.
2) Always attempt a helpful answer. If CONTEXT_DOCS contain partial information, use it and answer confidently.
3) For pricing questions: state the exact figures from context (e.g., "Gold membership is BDT 4,500/month") and briefly mention what is included.
4) For facility questions: describe the facility clearly. Reference international standards (FIFA, BWF, FIBA, Olympic) where available.
5) For academy questions: mention professional coaching, program structure, and age groups.
6) If CONTEXT_DOCS have NO relevant information, respond professionally:
   "I'm sorry, I don't have specific information on that right now. For accurate details, please contact our team:\n• Website: www.bashundharasportscity.com.bd\n• Email: info@bashundharasportscity.com.bd\n• We're open 5 AM – Midnight, every day of the year."
7) NEVER invent prices, dates, or facts not in CONTEXT_DOCS.
8) Handle negative or loaded questions calmly, with facts.
9) End with a relevant follow-up offer when natural — for example:
   - "Would you like details on our other membership plans?"
   - "Can I help you with anything else?"
10) Format: Use bullet points for lists. Keep responses concise (3–8 lines). Avoid excessive exclamations.
11) Always refer to the facility as "Bashundhara Sports City" or "BSC".
""".strip()


def generate_answer(user_query: str, matches: list) -> str:
    context = "\n\n".join([
        f"DOC_ID: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('id')}\n"
        f"SECTION: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('category', '')}\n"
        f"QUESTION: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('question', '')}\n"
        f"CONTENT: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('answer') or (m['metadata'] if isinstance(m, dict) else m.metadata).get('text', '')}\n"
        for m in matches
    ])

    logger.debug("Generating answer for query: %s | Context docs: %d", user_query, len(matches))

    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_ANSWER},
            {"role": "user", "content": f"FAQ_CONTEXT:\n{context}\n\nUSER_QUESTION:\n{user_query}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()