from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from django.contrib.auth.password_validation import validate_password
from django.db import IntegrityError
from django.db import transaction

from revix_backend.users.models import User

from .base import AuthenticationProvider

if TYPE_CHECKING:
    from collections.abc import Mapping

_DUMMY_PASSWORD_HASH = make_password("revix-invalid-login-timing-check")
EMAIL_ALREADY_REGISTERED = "email_already_registered"


class EmailAlreadyRegisteredError(ValueError):
    """Raised when registration attempts to reuse an email address."""


class PasswordProvider(AuthenticationProvider):
    def authenticate(self, credentials: Mapping[str, str]) -> User | None:
        email = credentials["email"]
        password = credentials["password"]
        user = User.objects.filter(email__iexact=email).first()
        if user is None:
            check_password(password, _DUMMY_PASSWORD_HASH)
            return None
        valid_password = (
            user.check_password(password) if user.has_usable_password() else False
        )
        if not user.has_usable_password():
            check_password(password, _DUMMY_PASSWORD_HASH)
        if not user.is_active or not valid_password:
            return None
        return user

    def register(self, *, email: str, password: str, name: str = "") -> User:
        normalized_email = User.objects.normalize_email(email.strip().casefold())
        if User.objects.filter(email__iexact=normalized_email).exists():
            msg = EMAIL_ALREADY_REGISTERED
            raise EmailAlreadyRegisteredError(msg)
        user = User(email=normalized_email, name=name.strip())
        validate_password(password, user=user)
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    email=normalized_email,
                    password=password,
                    name=name.strip(),
                )
        except IntegrityError as error:
            # Covers simultaneous registrations that pass the preflight query.
            msg = EMAIL_ALREADY_REGISTERED
            raise EmailAlreadyRegisteredError(msg) from error
