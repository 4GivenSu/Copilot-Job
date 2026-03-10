import random
import string
from datetime import datetime, timedelta, timezone

# In-memory store: {email: {"code": str, "expires_at": datetime}}
# NOTE: This store is process-local. On restart or with multiple workers/instances,
# stored codes will be lost. For production, replace with a shared store (e.g. Redis).
_verification_codes: dict[str, dict] = {}

CODE_EXPIRE_MINUTES = 5


def generate_code(length: int = 6) -> str:
    """Generate a random numeric verification code."""
    return "".join(random.choices(string.digits, k=length))


def store_code(email: str, code: str) -> None:
    """Store a verification code for the given email with an expiry time."""
    _verification_codes[email] = {
        "code": code,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=CODE_EXPIRE_MINUTES),
    }


def verify_code(email: str, code: str) -> bool:
    """Return True if the code matches and has not expired, then remove it."""
    entry = _verification_codes.get(email)
    if not entry:
        return False
    if datetime.now(timezone.utc) > entry["expires_at"]:
        _verification_codes.pop(email, None)
        return False
    if entry["code"] != code:
        return False
    _verification_codes.pop(email, None)
    return True
