from typing import List

def chunk_text(text: str, max_chars: int = 1200, overlap: int = 200) -> List[str]:
    text = text.strip()
    if len(text) <= max_chars:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunk = text[start:end].strip()
        chunks.append(chunk)
        if end == len(text):
            break
        start = max(0, end - overlap)

    return chunks