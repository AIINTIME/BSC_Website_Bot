import re

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')


def validate_name(value: str) -> tuple[bool, str]:
    v = value.strip()
    if len(v) < 2:
        return False, "Name must be at least 2 characters. Please enter your full name."
    if len(v) > 100:
        return False, "Name seems too long. Please enter a shorter name."
    return True, v


def validate_email(value: str) -> tuple[bool, str]:
    v = value.strip().lower()
    if not _EMAIL_RE.match(v):
        return False, "That doesn't look like a valid email (e.g. name@example.com). Please try again."
    return True, v


def validate_mobile(value: str) -> tuple[bool, str]:
    v = value.strip()
    digits = re.sub(r'\D', '', v)
    if len(digits) < 7 or len(digits) > 15:
        return False, "Please enter a valid mobile number (7–15 digits)."
    return True, v
