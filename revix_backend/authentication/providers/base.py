from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from typing import TYPE_CHECKING
from typing import cast

if TYPE_CHECKING:
    from collections.abc import Mapping

    from revix_backend.authentication.providers.password import PasswordProvider
    from revix_backend.users.models import User


class AuthenticationProvider(ABC):
    """Provider contract for password, Google, and future identity providers."""

    @abstractmethod
    def authenticate(self, credentials: Mapping[str, str]) -> User | None:
        """Return the matching active account or None for invalid credentials."""


class ProviderRegistry:
    def __init__(self, providers: dict[str, AuthenticationProvider]):
        self._providers = providers

    def get(self, name: str) -> AuthenticationProvider:
        return self._providers[name]

    def get_password(self) -> PasswordProvider:
        """Return the registered password provider, which also supports signup."""
        return cast("PasswordProvider", self._providers["password"])
