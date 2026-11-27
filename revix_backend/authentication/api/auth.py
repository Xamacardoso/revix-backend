import hmac

from django.utils import timezone
from ninja.security import HttpBearer

from revix_backend.authentication.models import AuthSession
from revix_backend.authentication.tokens import parse_token


class SessionBearerAuth(HttpBearer):
    def authenticate(self, request, token: str) -> AuthSession | None:
        parsed = parse_token(token)
        if parsed is None:
            return None
        session_id, supplied_digest = parsed
        try:
            session = AuthSession.objects.select_related("user").get(pk=session_id)
        except AuthSession.DoesNotExist:
            return None
        if (
            session.revoked_at is not None
            or session.access_expires_at <= timezone.now()
            or not session.user.is_active
            or not hmac.compare_digest(session.access_token_digest, supplied_digest)
        ):
            return None
        return session


session_bearer_auth = SessionBearerAuth()
