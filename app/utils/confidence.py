"""
Confidence scoring helpers for BSC Website Bot.
Translates raw vector similarity scores into human-readable labels.
"""

# Thresholds (tuned to Pinecone cosine similarity with text-embedding-3-small)
_HIGH = 0.85
_MEDIUM = 0.70
_LOW = 0.55


def score_to_label(score: float) -> str:
    """
    Convert a float similarity score to a confidence label.

    Returns:
        "high"      — score >= 0.85
        "medium"    — score >= 0.70
        "low"       — score >= 0.55
        "uncertain" — score < 0.55
    """
    if score >= _HIGH:
        return "high"
    elif score >= _MEDIUM:
        return "medium"
    elif score >= _LOW:
        return "low"
    else:
        return "uncertain"


def is_confident_enough(score: float, threshold: float | None = None) -> bool:
    """
    Returns True if the score meets or exceeds the given threshold.
    Defaults to the MEDIUM threshold if none is provided.
    """
    return score >= (threshold if threshold is not None else _MEDIUM)
