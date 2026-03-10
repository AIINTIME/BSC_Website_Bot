"""
Redis-backed state machine for the contact-detail collection flow.

States:  name → email → mobile → address → confirm → done
"""
import json
from app.services.memory_store_redis import redis_client
from app.core.config import settings
from app.services.contact_validator import validate_name, validate_email, validate_mobile
from app.services.sheets_service import write_contact


def _state_key(session_id: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:contact:{session_id}:state"


def _data_key(session_id: str) -> str:
    return f"{settings.REDIS_KEY_PREFIX}:contact:{session_id}:data"


_TTL = settings.REDIS_TTL_SECONDS


# ── Public helpers ────────────────────────────────────────────────────────────

def get_contact_state(session_id: str) -> str | None:
    return redis_client.get(_state_key(session_id))


def set_contact_state(session_id: str, state: str) -> None:
    redis_client.setex(_state_key(session_id), _TTL, state)


def get_contact_data(session_id: str) -> dict:
    raw = redis_client.get(_data_key(session_id))
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def set_contact_data(session_id: str, data: dict) -> None:
    redis_client.setex(_data_key(session_id), _TTL, json.dumps(data))


def clear_contact_flow(session_id: str) -> None:
    redis_client.delete(_state_key(session_id))
    redis_client.delete(_data_key(session_id))


# ── Flow entry point ──────────────────────────────────────────────────────────

def start_contact_flow(session_id: str) -> str:
    """Initialise the flow and return the first prompt."""
    set_contact_state(session_id, "name")
    set_contact_data(session_id, {})
    return (
        "Welcome to **Bashundhara Sports City**! 🏆\n\n"
        "Before I assist you, may I take a few quick details?\n\n"
        "What is your **full name**?"
    )


# ── Step handler ─────────────────────────────────────────────────────────────

def handle_contact_step(session_id: str, user_input: str) -> str:
    """Process one user reply in the contact flow. Returns the next bot message."""
    state = get_contact_state(session_id)
    data = get_contact_data(session_id)
    text = user_input.strip()

    # Allow cancel at any point
    if text.lower() in ("cancel", "abort", "exit"):
        clear_contact_flow(session_id)
        set_contact_state(session_id, "done")
        return (
            "No problem! I've skipped the details form.\n\n"
            "How can I help you with Bashundhara Sports City today?"
        )

    # ── Name (required) ───────────────────────────────────────────────────────
    if state == "name":
        if text.lower() == "skip":
            return "Your name is required. Please enter your **full name**."
        ok, val = validate_name(text)
        if not ok:
            return val
        data["name"] = val
        set_contact_data(session_id, data)
        set_contact_state(session_id, "email")
        return f"Nice to meet you, **{val}**! 👋\n\nWhat is your **email address**?"

    # ── Email (required) ──────────────────────────────────────────────────────
    if state == "email":
        if text.lower() == "skip":
            return "Your email address is required. Please enter a valid email (e.g. name@example.com)."
        ok, val = validate_email(text)
        if not ok:
            return val
        data["email"] = val
        set_contact_data(session_id, data)
        set_contact_state(session_id, "mobile")
        return "Got it! What is your **mobile number**?"

    # ── Mobile (required) ─────────────────────────────────────────────────────
    if state == "mobile":
        if text.lower() == "skip":
            return "Your mobile number is required. Please enter a valid number (e.g. 01712345678)."
        ok, val = validate_mobile(text)
        if not ok:
            return val
        data["mobile"] = val
        set_contact_data(session_id, data)
        set_contact_state(session_id, "address")
        return "Almost done! What is your **address**?\n*(Type **skip** to leave this blank)*"

    # ── Address ───────────────────────────────────────────────────────────────
    if state == "address":
        data["address"] = "" if text.lower() == "skip" else text
        set_contact_data(session_id, data)
        set_contact_state(session_id, "confirm")
        addr_display = data["address"] if data["address"] else "*(not provided)*"
        return (
            "Please confirm your details:\n\n"
            f"• **Name:** {data['name']}\n"
            f"• **Email:** {data['email']}\n"
            f"• **Mobile:** {data['mobile']}\n"
            f"• **Address:** {addr_display}\n\n"
            "Type **yes** to confirm or **no** to start over."
        )

    # ── Confirm ───────────────────────────────────────────────────────────────
    if state == "confirm":
        if text.lower() in ("yes", "y", "confirm", "ok", "okay"):
            try:
                write_contact(
                    name=data.get("name", ""),
                    email=data.get("email", ""),
                    mobile=data.get("mobile", ""),
                    address=data.get("address", ""),
                    session_id=session_id,
                )
            except Exception as e:
                print(f"[Sheets] Write failed: {e}")
            set_contact_state(session_id, "done")
            return (
                f"Thank you, **{data.get('name', '')}**! Your details have been saved. ✅\n\n"
                "Now, how can I help you with Bashundhara Sports City today?"
            )
        if text.lower() in ("no", "n", "restart", "redo"):
            set_contact_state(session_id, "name")
            set_contact_data(session_id, {})
            return "No problem! Let's start over.\n\nWhat is your **full name**?"
        return "Please type **yes** to confirm or **no** to start over."

    # Fallback (state == "done" or unexpected)
    return "How can I help you with Bashundhara Sports City today?"
