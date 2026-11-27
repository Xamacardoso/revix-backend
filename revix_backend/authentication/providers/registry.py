from .base import ProviderRegistry
from .password import PasswordProvider

providers = ProviderRegistry({"password": PasswordProvider()})
