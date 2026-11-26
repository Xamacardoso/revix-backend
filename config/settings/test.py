"""
With these settings, tests run faster.
"""

import os

# The test suite must be runnable without a PostgreSQL server. Values are set
# before base settings are imported because its PostgreSQL configuration reads
# the required POSTGRES_* variables during startup.
os.environ.setdefault("POSTGRES_DB", "revix_backend_test")
os.environ.setdefault("POSTGRES_USER", "revix_backend_test")
os.environ.setdefault("POSTGRES_PASSWORD", "test-only")

from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="x0zUkqJ2Prf9hIgqTQghcFZJxWoRkkzm1t3VjuW3J2hdc0wAhqxrDMKHLznLfpMS",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"
API_DOCS_ENABLED = True
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
MEDIA_URL = "http://media.testserver/"
# Your stuff...
# ------------------------------------------------------------------------------
