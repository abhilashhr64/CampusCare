import secrets
import hashlib
from typing import Tuple
import bcrypt
import pyotp
from src.core.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt with salt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash in constant time."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def generate_session_token() -> Tuple[str, str]:
    """Generates a high-entropy 256-bit session token.
    Returns:
        (raw_token, token_hash)
    Only token_hash is persisted in database (ADR-003).
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    return raw_token, token_hash


def hash_token(token: str) -> str:
    """Hash a session or verification token using SHA-256."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return secrets.compare_digest(val1, val2)


# Multi-Factor Authentication (TOTP - RFC 6238)
def generate_totp_secret() -> str:
    """Generate a base32 TOTP secret for staff MFA."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str) -> str:
    """Generate a provisioning URI for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=settings.MFA_ISSUER)


def verify_totp_code(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code with a 1-step window."""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
