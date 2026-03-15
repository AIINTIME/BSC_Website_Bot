import re

_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')

# Only allow letters, spaces, hyphens, apostrophes, and periods (for initials)
_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z\s'\-\.]*$")

# Common words that indicate the user typed a query instead of their name
_QUERY_KEYWORDS = {
    "membership", "plan", "plans", "price", "prices", "cost", "costs",
    "offer", "offers", "how", "what", "when", "where", "why", "which",
    "who", "can", "do", "does", "is", "are", "tell", "show", "about",
    "information", "info", "help", "package", "packages", "fee", "fees",
    "gym", "pool", "sport", "sports", "facility", "facilities", "schedule",
    "timing", "timings", "contact", "location", "discount", "class", "classes",
    "monthly", "annual", "yearly", "weekly", "daily", "register", "registration",
    "book", "booking", "enquiry", "inquiry", "details", "available", "availability",
}


def validate_name(value: str) -> tuple[bool, str]:
    v = value.strip()
    if len(v) < 2:
        return False, "Name must be at least 2 characters. Please enter your **full name**."
    if len(v) > 100:
        return False, "Name seems too long. Please enter a shorter name."

    # Must only contain letters, spaces, hyphens, apostrophes, or periods
    if not _NAME_RE.match(v):
        return False, "That doesn't look like a valid name. Please enter your **full name** using letters only (e.g. John Smith)."

    # Detect if the input looks like a query rather than a name
    words = {w.lower() for w in v.split()}
    if words & _QUERY_KEYWORDS:
        return False, "That looks like a question, not a name. 😊 Please enter your **full name** (e.g. John Smith)."

    # A name shouldn't be more than 5 words
    if len(v.split()) > 5:
        return False, "That seems too long for a name. Please enter your **full name**."

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


def validate_address(value: str) -> tuple[bool, str]:
    v = value.strip()
    if len(v) < 5:
        return False, "Address is too short. Please enter your **full address** (e.g. House 5, Road 3, Gulshan, Dhaka)."
    if len(v) > 200:
        return False, "Address is too long. Please shorten it."

    # Must contain at least one letter or digit
    if not re.search(r'[A-Za-z0-9]', v):
        return False, "Please enter a valid address."

    # Reject if more than 40 % of words look like a query
    words = [w.lower().rstrip('?.,!') for w in v.split()]
    if words:
        query_hits = sum(1 for w in words if w in _QUERY_KEYWORDS)
        if query_hits / len(words) > 0.4:
            return False, (
                "That looks like a question, not an address. 😊 "
                "Please enter your **address** (e.g. House 5, Road 3, Gulshan, Dhaka) "
                "or click **Skip** to skip."
            )

    return True, v
