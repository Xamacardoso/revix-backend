import hashlib
import hmac

from django.conf import settings
from django.core.cache import cache


def _client_ip(request) -> str:
    header = settings.AUTH_CLIENT_IP_HEADER
    if header:
        # Trust only a proxy header explicitly configured by the deployment.
        return request.META.get(header, "unknown")[:128]
    return request.META.get("REMOTE_ADDR", "unknown")[:128]


def _cache_key(action: str, dimension: str, identity: str) -> str:
    material = f"{action}:{dimension}:{identity}".encode()
    digest = hmac.new(
        settings.SECRET_KEY.encode(),
        material,
        hashlib.sha256,
    ).hexdigest()
    return f"revix:auth:rate:{digest}"


def is_rate_limited(request, action: str, *, subject: str | None = None) -> bool:
    """Increment fixed-window counters; cache errors fail closed for auth routes."""
    limits = settings.AUTH_RATE_LIMITS[action]
    for dimension, (limit, window_seconds) in limits.items():
        if dimension == "ip":
            identity = _client_ip(request)
        elif dimension == "email" and subject:
            identity = subject.strip().casefold()
        else:
            continue

        key = _cache_key(action, dimension, identity)
        if cache.add(key, 1, timeout=window_seconds):
            count = 1
        else:
            try:
                count = cache.incr(key)
            except ValueError:
                # The key may expire between add() and incr(). Recreate it.
                if cache.add(key, 1, timeout=window_seconds):
                    count = 1
                else:
                    count = cache.incr(key)
        if count > limit:
            return True
    return False
