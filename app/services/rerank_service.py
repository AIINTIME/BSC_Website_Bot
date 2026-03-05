import json
import re
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_RERANK = """
You are selecting knowledge base documents to answer a user's question about Bashundhara Sports City (BSC).

Return ONLY a valid JSON object (no markdown, no code fences) in this schema:
{
  "selected_ids": ["BSCBOT_DOC_3_CH_1", "BSCBOT_DOC_7_CH_2"],
  "reason": "short reason"
}

Rules:
- Each candidate has: id, category (page section), and snippet (preview of actual content).
- Be INCLUSIVE: select every document whose snippet is relevant OR partially relevant to the query topic.
- ALWAYS prefer to include more documents (2–4) over fewer. More context = better answers.
- Include a document if its snippet covers the same topic area (e.g., membership pricing, facility details, academy info, contact/location) even if it is not a perfect word-for-word match.
- The detailed content pages (pages.membership, pages.facilities, pages.academies) are more valuable than SEO or home page summaries — prefer them when present.
- Only return empty selected_ids if ALL candidates are completely unrelated to BSC or the user's topic (e.g., user asks about unrelated topics).
- IDs must be exactly as provided in candidates.
""".strip()

def _strip_json_fences(text: str) -> str:
    # removes ```json ... ``` or ``` ... ```
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()

def rerank(user_query: str, matches: list, top_n: int):
    candidates = []
    for m in matches:
        md = m["metadata"] if isinstance(m, dict) else m.metadata
        raw_text = md.get("text") or md.get("answer") or md.get("question") or ""
        candidates.append({
            "id": md.get("id"),
            "category": md.get("category", ""),
            "snippet": raw_text[:400],
        })

    payload = {
        "user_query": user_query,
        "candidates": candidates[: min(len(candidates), 20)],
        "max_select": top_n
    }

    resp = client.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_RERANK},
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}
        ],
        temperature=0
    )

    raw = resp.choices[0].message.content.strip()
    cleaned = _strip_json_fences(raw)

    try:
        data = json.loads(cleaned)
        selected = data.get("selected_ids", [])
        reason = data.get("reason", "")

        # enforce max_select and remove nulls
        selected = [str(x).strip() for x in selected if x]
        selected = selected[:top_n]

        return selected, reason

    except Exception as e:
        # Fail-safe: similarity top_n
        fallback = []
        for m in matches[:top_n]:
            md = m["metadata"] if isinstance(m, dict) else m.metadata
            if md.get("id"):
                fallback.append(md.get("id"))

        return fallback, f"fallback_rerank_parse_error: {type(e).__name__}"