import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class AuthSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auth_sessions",
    )
    access_token_digest = models.CharField(max_length=64)
    refresh_token_digest = models.CharField(max_length=64)
    access_expires_at = models.DateTimeField()
    refresh_expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["user", "revoked_at"],
                name="auth_session_user_revoked_idx",
            ),
            models.Index(
                fields=["refresh_expires_at"],
                name="auth_session_refresh_exp_idx",
            ),
        ]

    def __str__(self) -> str:
        return f"Authentication session {self.pk} for user {self.user_id}"


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens",
    )
    token_digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"], name="auth_reset_user_exp_idx"),
        ]

    def __str__(self) -> str:
        return f"Password reset token {self.pk} for user {self.user_id}"
