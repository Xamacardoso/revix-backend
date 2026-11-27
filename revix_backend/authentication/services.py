import hmac
import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.core.mail import send_mail
from django.db import transaction
from django.utils import timezone

from revix_backend.users.models import User

from .models import AuthSession
from .models import PasswordResetToken
from .tokens import digest_recovery_token
from .tokens import issue_recovery_token
from .tokens import issue_token
from .tokens import parse_token

logger = logging.getLogger(__name__)


def create_session(user: User) -> tuple[AuthSession, str, str]:
    access_token, access_digest, session_id = issue_token()
    refresh_token, refresh_digest, _ = issue_token(identifier=session_id)
    now = timezone.now()
    session = AuthSession.objects.create(
        id=session_id,
        user=user,
        access_token_digest=access_digest,
        refresh_token_digest=refresh_digest,
        access_expires_at=now
        + timedelta(seconds=settings.AUTH_ACCESS_TOKEN_TTL_SECONDS),
        refresh_expires_at=now
        + timedelta(seconds=settings.AUTH_REFRESH_TOKEN_TTL_SECONDS),
    )
    return session, access_token, refresh_token


def rotate_session(refresh_token: str) -> tuple[AuthSession, str, str] | None:
    parsed = parse_token(refresh_token)
    if parsed is None:
        return None
    session_id, supplied_digest = parsed
    with transaction.atomic():
        try:
            session = (
                AuthSession.objects.select_for_update()
                .select_related("user")
                .get(pk=session_id)
            )
        except AuthSession.DoesNotExist:
            return None
        now = timezone.now()
        if (
            session.revoked_at is not None
            or session.refresh_expires_at <= now
            or not session.user.is_active
        ):
            return None
        if not hmac.compare_digest(session.refresh_token_digest, supplied_digest):
            # Reuse of an older refresh token revokes the whole credential family.
            session.revoked_at = now
            session.save(update_fields=["revoked_at", "updated_at"])
            return None

        access_token, access_digest, _ = issue_token(identifier=session_id)
        new_refresh_token, refresh_digest, _ = issue_token(identifier=session_id)
        session.access_token_digest = access_digest
        session.refresh_token_digest = refresh_digest
        session.access_expires_at = now + timedelta(
            seconds=settings.AUTH_ACCESS_TOKEN_TTL_SECONDS,
        )
        session.refresh_expires_at = now + timedelta(
            seconds=settings.AUTH_REFRESH_TOKEN_TTL_SECONDS,
        )
        session.save(
            update_fields=[
                "access_token_digest",
                "refresh_token_digest",
                "access_expires_at",
                "refresh_expires_at",
                "updated_at",
            ],
        )
        return session, access_token, new_refresh_token


def request_password_reset(email: str) -> None:
    user = User.objects.filter(email__iexact=email.strip(), is_active=True).first()
    if user is None:
        return

    now = timezone.now()
    secret, token_digest = issue_recovery_token()
    PasswordResetToken.objects.filter(user=user, consumed_at__isnull=True).update(
        consumed_at=now,
    )
    PasswordResetToken.objects.create(
        user=user,
        token_digest=token_digest,
        expires_at=now
        + timedelta(seconds=settings.AUTH_PASSWORD_RESET_TOKEN_TTL_SECONDS),
    )
    try:
        send_mail(
            subject="Redefinição de senha do Revix",
            message=(
                "Use o código de uso único abaixo para redefinir sua senha "
                "no Revix.\n\n"
                f"{secret}\n\n"
                "Se você não solicitou esta alteração, ignore esta mensagem."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception:  # noqa: BLE001
        # The public response remains identical for existing and unknown emails.
        # Django's configured mail backend reports delivery failures operationally.
        logger.warning("Password reset email delivery failed for user id %s", user.pk)
        return


def reset_password(*, token: str, new_password: str) -> bool:
    token_digest = digest_recovery_token(token)
    with transaction.atomic():
        try:
            challenge = (
                PasswordResetToken.objects.select_for_update()
                .select_related("user")
                .get(
                    token_digest=token_digest,
                    consumed_at__isnull=True,
                    expires_at__gt=timezone.now(),
                    user__is_active=True,
                )
            )
        except PasswordResetToken.DoesNotExist:
            return False

        user = challenge.user
        validate_password(new_password, user=user)
        now = timezone.now()
        user.set_password(new_password)
        user.save(update_fields=["password"])
        AuthSession.objects.filter(user=user, revoked_at__isnull=True).update(
            revoked_at=now,
        )
        PasswordResetToken.objects.filter(user=user, consumed_at__isnull=True).update(
            consumed_at=now,
        )
    return True
