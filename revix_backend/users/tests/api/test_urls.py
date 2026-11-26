from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import resolve
from django.urls import reverse

if TYPE_CHECKING:
    from revix_backend.users.models import User


def test_user_detail(user: User):
    assert (
        reverse("api:retrieve_user", kwargs={"pk": user.pk})
        == f"/api/v1/users/{user.pk}/"
    )
    assert resolve(f"/api/v1/users/{user.pk}/").view_name == "api:retrieve_user"


def test_user_list():
    assert reverse("api:list_users") == "/api/v1/users/"
    assert resolve("/api/v1/users/").view_name == "api:list_users"


def test_current_user():
    assert reverse("api:retrieve_current_user") == "/api/v1/users/me/"
    assert resolve("/api/v1/users/me/").view_name == "api:retrieve_current_user"


def test_update_user():
    assert reverse("api:update_user", kwargs={"pk": 123}) == "/api/v1/users/123/"
    assert resolve("/api/v1/users/123/").view_name == "api:retrieve_user"
