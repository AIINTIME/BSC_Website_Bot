import json
import re
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM_RERANK = """
You are ranking FAQ entries for relevance to the user's question.

Return ONLY a valid JSON object (no markdown, no code fences) in this schema:
{
  "selected_ids": ["Q2", "Q17"],
  "reason": "short reason"
}

Rules:
- Select the most relevant FAQ IDs (max N).
- Prefer direct answers over tangential matches.
- If none are truly relevant, return {"selected_ids": [], "reason": "..."}.
- IDs must be exactly as provided in candidates (e.g., "Q2").
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
        candidates.append({
            "id": md.get("id"),  # MUST exist (ensure ingestion stores it)
            "question": md.get("question", ""),
            "category": md.get("category", ""),
            "keywords": md.get("keywords", []),
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