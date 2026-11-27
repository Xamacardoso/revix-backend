import hashlib
import hmac
import secrets
import uuid

from django.conf import settings

MAX_TOKEN_SECRET_LENGTH = 128


def _digest(purpose: str, secret: str) -> str:
    message = f"revix:{purpose}:{secret}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()


def issue_token(identifier: uuid.UUID | None = None) -> tuple[str, str, uuid.UUID]:
    token_id = identifier or uuid.uuid4()
    secret = secrets.token_urlsafe(32)
    return f"{token_id}.{secret}", _digest("session", f"{token_id}.{secret}"), token_id


def parse_token(token: str) -> tuple[uuid.UUID, str] | None:
    try:
        identifier, secret = token.split(".", maxsplit=1)
        token_id = uuid.UUID(identifier)
    except ValueError, AttributeError:
        return None
    if not secret or len(secret) > MAX_TOKEN_SECRET_LENGTH:
        return None
    return token_id, _digest("session", f"{token_id}.{secret}")


def digest_recovery_token(token: str) -> str:
    return _digest("password-reset", token)


def issue_recovery_token() -> tuple[str, str]:
    secret = secrets.token_urlsafe(32)
    return secret, digest_recovery_token(secret)
