import json
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth.hashers import identify_hasher
from django.core import mail
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone

from revix_backend.authentication.models import AuthSession
from revix_backend.authentication.models import PasswordResetToken
from revix_backend.authentication.tokens import digest_recovery_token
from revix_backend.users.models import User

pytestmark = pytest.mark.django_db

PASSWORD = "Safe-Revix-Test-Password-2026!"  # noqa: S105
ACCESS_TOKEN_TTL_SECONDS = 900


@pytest.fixture(autouse=True)
def clear_rate_limit_cache():
    cache.clear()


def post_json(client, url: str, payload: dict, **kwargs):
    return client.post(
        url,
        data=json.dumps(payload),
        content_type="application/json",
        **kwargs,
    )


def register(client, email="person@example.com", password=PASSWORD):
    return post_json(
        client,
        "/api/v1/auth/register",
        {"email": email, "password": password, "name": "Revix Person"},
    )


def test_register_hashes_password_and_only_stores_token_digests(client):
    with override_settings(
        PASSWORD_HASHERS=["django.contrib.auth.hashers.Argon2PasswordHasher"],
    ):
        response = register(client)
        assert response.status_code == HTTPStatus.CREATED
        body = response.json()
        user = User.objects.get(email="person@example.com")
        session = AuthSession.objects.get(user=user)
        assert identify_hasher(user.password).algorithm == "argon2"
        assert user.password != PASSWORD
        second_user = User.objects.create_user(
            email="second@example.com",
            password=PASSWORD,
        )
        assert second_user.password != user.password
        assert body["access_token"] not in session.access_token_digest
        assert body["refresh_token"] not in session.refresh_token_digest
        assert 0 < body["expires_in"] <= ACCESS_TOKEN_TTL_SECONDS


def test_login_uses_generic_error_and_returns_bearer_tokens(client):
    user = User.objects.create_user(email="person@example.com", password=PASSWORD)

    invalid = post_json(
        client,
        "/api/v1/auth/login",
        {"email": user.email, "password": "wrong-password"},
    )
    valid = post_json(
        client,
        "/api/v1/auth/login",
        {"email": user.email, "password": PASSWORD},
    )

    assert invalid.status_code == HTTPStatus.UNAUTHORIZED
    assert invalid.json() == {"detail": "Invalid email or password."}
    assert valid.status_code == HTTPStatus.OK
    assert valid.json()["token_type"] == "Bearer"  # noqa: S105


def test_registration_rejects_weak_password_and_duplicate_email(client):
    weak = register(client, password="123456789012")  # noqa: S106
    assert weak.status_code == HTTPStatus.UNPROCESSABLE_ENTITY

    assert register(client).status_code == HTTPStatus.CREATED
    duplicate = register(client, email="PERSON@example.com")
    assert duplicate.status_code == HTTPStatus.CONFLICT


def test_expired_access_token_is_rejected(client):
    pair = register(client).json()
    session = AuthSession.objects.get()
    session.access_expires_at = timezone.now() - timedelta(seconds=1)
    session.save(update_fields=["access_expires_at"])

    response = client.get(
        "/api/v1/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {pair['access_token']}",
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


def test_bearer_identity_logout_and_refresh_rotation(client):
    registration = register(client)
    assert registration.status_code == HTTPStatus.CREATED
    initial = registration.json()

    current = client.get(
        "/api/v1/auth/me",
        HTTP_AUTHORIZATION=f"Bearer {initial['access_token']}",
    )
    assert current.status_code == HTTPStatus.OK
    assert current.json()["email"] == "person@example.com"

    refreshed = post_json(
        client,
        "/api/v1/auth/refresh",
        {"refresh_token": initial["refresh_token"]},
    )
    assert refreshed.status_code == HTTPStatus.OK
    rotated = refreshed.json()
    assert rotated["refresh_token"] != initial["refresh_token"]
    assert (
        client.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {initial['access_token']}",
        ).status_code
        == HTTPStatus.UNAUTHORIZED
    )

    logout = client.post(
        "/api/v1/auth/logout",
        HTTP_AUTHORIZATION=f"Bearer {rotated['access_token']}",
    )
    assert logout.status_code == HTTPStatus.NO_CONTENT
    assert (
        client.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {rotated['access_token']}",
        ).status_code
        == HTTPStatus.UNAUTHORIZED
    )


def test_refresh_token_reuse_revokes_session(client):
    initial = register(client).json()
    assert (
        post_json(
            client,
            "/api/v1/auth/refresh",
            {"refresh_token": initial["refresh_token"]},
        ).status_code
        == HTTPStatus.OK
    )

    replay = post_json(
        client,
        "/api/v1/auth/refresh",
        {"refresh_token": initial["refresh_token"]},
    )
    assert replay.status_code == HTTPStatus.UNAUTHORIZED
    assert AuthSession.objects.get().revoked_at is not None


def test_password_reset_is_generic_single_use_and_revokes_sessions(client):
    registration = register(client)
    user = User.objects.get(email="person@example.com")
    initial = registration.json()

    known = post_json(
        client,
        "/api/v1/auth/password-reset/request",
        {"email": user.email},
    )
    unknown = post_json(
        client,
        "/api/v1/auth/password-reset/request",
        {"email": "unknown@example.com"},
    )
    assert known.status_code == unknown.status_code == HTTPStatus.ACCEPTED
    assert known.json() == unknown.json()
    secret = mail.outbox[0].body.splitlines()[2]
    reset_record = PasswordResetToken.objects.get(user=user)
    assert reset_record.token_digest == digest_recovery_token(secret)
    assert secret not in reset_record.token_digest

    completed = post_json(
        client,
        "/api/v1/auth/password-reset/confirm",
        {"token": secret, "new_password": "New-Safe-Revix-Password-2026!"},
    )
    assert completed.status_code == HTTPStatus.OK
    assert user.__class__.objects.get(pk=user.pk).check_password(
        "New-Safe-Revix-Password-2026!",
    )
    assert AuthSession.objects.get().revoked_at is not None
    replay = post_json(
        client,
        "/api/v1/auth/password-reset/confirm",
        {"token": secret, "new_password": "Another-Safe-Password-2026!"},
    )
    assert replay.status_code == HTTPStatus.BAD_REQUEST
    assert (
        client.get(
            "/api/v1/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {initial['access_token']}",
        ).status_code
        == HTTPStatus.UNAUTHORIZED
    )


def test_expired_password_reset_token_cannot_be_used(client):
    User.objects.create_user(email="person@example.com", password=PASSWORD)
    post_json(
        client,
        "/api/v1/auth/password-reset/request",
        {"email": "person@example.com"},
    )
    token = mail.outbox[0].body.splitlines()[2]
    PasswordResetToken.objects.update(expires_at=timezone.now() - timedelta(seconds=1))

    response = post_json(
        client,
        "/api/v1/auth/password-reset/confirm",
        {"token": token, "new_password": "New-Safe-Revix-Password-2026!"},
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


def test_authentication_rate_limit_returns_429(client):
    cache.clear()
    User.objects.create_user(email="person@example.com", password=PASSWORD)
    limits = {"login": {"ip": (1, 60), "email": (1, 60)}}
    with override_settings(AUTH_RATE_LIMITS=limits):
        first = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "person@example.com", "password": "wrong-password"},
        )
        second = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "person@example.com", "password": "wrong-password"},
        )

    assert first.status_code == HTTPStatus.UNAUTHORIZED
    assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_login_rate_limit_is_scoped_to_email_as_well_as_ip(client):
    cache.clear()
    User.objects.create_user(email="person@example.com", password=PASSWORD)
    limits = {"login": {"ip": (10, 60), "email": (1, 60)}}
    with override_settings(AUTH_RATE_LIMITS=limits):
        first = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "person@example.com", "password": "wrong-password"},
            REMOTE_ADDR="203.0.113.1",
        )
        second = post_json(
            client,
            "/api/v1/auth/login",
            {"email": "person@example.com", "password": "wrong-password"},
            REMOTE_ADDR="203.0.113.2",
        )

    assert first.status_code == HTTPStatus.UNAUTHORIZED
    assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_password_reset_rate_limit_returns_429_for_same_ip(client):
    cache.clear()
    limits = {"password_reset_request": {"ip": (1, 60), "email": (10, 60)}}
    with override_settings(AUTH_RATE_LIMITS=limits):
        first = post_json(
            client,
            "/api/v1/auth/password-reset/request",
            {"email": "unknown@example.com"},
        )
        second = post_json(
            client,
            "/api/v1/auth/password-reset/request",
            {"email": "another@example.com"},
        )

    assert first.status_code == HTTPStatus.ACCEPTED
    assert second.status_code == HTTPStatus.TOO_MANY_REQUESTS


def test_auth_routes_are_in_openapi_schema(admin_client):
    response = admin_client.get(reverse("api:openapi-json"))

    assert response.status_code == HTTPStatus.OK
    paths = response.json()["paths"]
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/password-reset/confirm" in paths
