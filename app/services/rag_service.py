# from openai import OpenAI
# from app.core.config import settings

# client = OpenAI(api_key=settings.OPENAI_API_KEY)

# def generate_answer(user_query: str, faqs: list):

#     context = "\n\n".join([
#         f"Q: {m['metadata']['question']}\nA: {m['metadata']['answer']}"
#         for m in faqs
#     ])

#     system_prompt = """
#     You are HIT official assistant.
#     Answer ONLY using the provided FAQ context.
#     If answer is not in context, say:
#     "I do not have that information in the official FAQs.
#     Please contact Admissions or use the Contact page."
#     Do not guess. Do not fabricate.
#     """

#     response = client.chat.completions.create(
#         model=settings.LLM_MODEL,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{user_query}"}
#         ],
#         temperature=0
#     )

#     return response.choices[0].message.content



# Rewrite
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_ANSWER = """
You are HIT's official FAQ assistant.

Rules (strict):
1) Answer ONLY using FAQ_CONTEXT.
2) Do NOT guess, do NOT add new facts.
3) If FAQ_CONTEXT lacks the required information, respond exactly:
   "I do not have that information in the official FAQs. Please contact Admissions or use the Contact page."
4) If user uses negative/loaded wording ("bad", "fake", "unsafe"), respond with neutral factual statements
   from FAQ_CONTEXT and avoid adopting the user's framing unless FAQ explicitly states it.
5) Keep response concise (3–7 lines).
""".strip()

def generate_answer(user_query: str, matches: list) -> str:
    context = "\n\n".join([
        f"FAQ_ID: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('id')}\n"
        f"FAQ_Q: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('question')}\n"
        f"FAQ_A: {(m['metadata'] if isinstance(m, dict) else m.metadata).get('answer')}\n"
        for m in matches
    ])

    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_ANSWER},
            {"role": "user", "content": f"FAQ_CONTEXT:\n{context}\n\nUSER_QUESTION:\n{user_query}"}
        ],
        temperature=0
    )
    return resp.choices[0].message.content.strip()