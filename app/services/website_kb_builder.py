import re
from typing import Any, Dict, List, Tuple

# Keys we typically DON'T want to index (adjust as needed)
SKIP_KEYS = {
    "id", "uuid", "slug", "icon", "image", "img", "logo", "href", "url",
    "cta", "button", "buttons", "links", "social", "metadata",
}

def _clean_text(s: str) -> str:
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _is_useful_text(s: str) -> bool:
    s = _clean_text(s)
    if len(s) < 20:
        return False
    # avoid pure symbols
    if re.fullmatch(r"[\W_]+", s):
        return False
    return True

def _walk_json(obj: Any, path: str = "") -> List[Tuple[str, str]]:
    """
    Returns list of (path, text_value) for all useful strings in JSON.
    """
    results: List[Tuple[str, str]] = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = f"{path}.{k}" if path else k

            # Skip certain keys (often non-human text)
            if k.lower() in SKIP_KEYS:
                continue

            results.extend(_walk_json(v, kp))

    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            kp = f"{path}[{i}]"
            results.extend(_walk_json(item, kp))

    elif isinstance(obj, str):
        if _is_useful_text(obj):
            results.append((path, _clean_text(obj)))

    return results

def build_documents(site_json: Dict[str, Any], client: str) -> List[Dict[str, Any]]:
    """
    Convert the entire website JSON into logical documents grouped by high-level page paths.
    Output format aligns with your RAG ingestion expectations.
    """
    pairs = _walk_json(site_json)

    # Group content by top-level page if possible
    # Example path: pages.membership.faqs[0].question -> group_key = pages.membership
    grouped: Dict[str, List[Tuple[str, str]]] = {}
    for p, t in pairs:
        parts = p.split(".")
        group_key = ".".join(parts[:2]) if len(parts) >= 2 else (parts[0] if parts else "root")
        grouped.setdefault(group_key, []).append((p, t))

    docs: List[Dict[str, Any]] = []
    doc_no = 0
    for group_key, items in grouped.items():
        doc_no += 1
        # Combine into a structured document text so the model sees context + labels
        lines = [f"CLIENT: {client}", f"SECTION: {group_key}", ""]
        for p, t in items:
            lines.append(f"{p}: {t}")
        full_text = "\n".join(lines)

        docs.append({
            "id": f"{client.upper()}_DOC_{doc_no}",
            "category": group_key,
            "question": f"Website content for {group_key}",   # keeps your schema consistent
            "answer": full_text,
            "chunk_text": full_text,
            "source": "website_json",
            "tags": [client, "website_kb"],
            "path_group": group_key,
        })

    return docs