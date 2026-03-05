"""
Text utility helpers for BSC Website Bot.
"""
import re


def normalize_query(text: str) -> str:
    """
    Normalize a user query for processing:
    - Strip leading/trailing whitespace
    - Collapse internal whitespace to single spaces
    - Lowercase for consistency
    """
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    return text.lower()


def truncate(text: str, max_chars: int = 500, suffix: str = "…") -> str:
    """
    Safely truncate a string to max_chars, appending suffix if truncated.
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars - len(suffix)].rstrip() + suffix


def clean_whitespace(text: str) -> str:
    """
    Collapse all whitespace (including newlines and tabs) to single spaces.
    """
    return re.sub(r"\s+", " ", text).strip()


def is_empty_or_short(text: str, min_length: int = 10) -> bool:
    """
    Returns True if text is empty or shorter than min_length after stripping.
    """
    return len(text.strip()) < min_length
