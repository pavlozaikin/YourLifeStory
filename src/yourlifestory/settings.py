"""
Django settings for yourlifestory project.
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent


def load_env_file(env_path):
    if not env_path.exists():
        return

    for raw_line in env_path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        os.environ.setdefault(key, value)


def env_required(name):
    value = os.getenv(name)
    if not value:
        raise ImproperlyConfigured(
            f"Missing required environment variable: {name}. "
            f"Configure PostgreSQL access in {PROJECT_DIR / '.env'} or export it in the shell."
        )
    return value


def env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


load_env_file(PROJECT_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-c0nbi&q=_1w9eu&!23andp$r5u2f88=(x0=rttf70bmaoz43cq")
DEBUG = True
ALLOWED_HOSTS = []


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core.apps.CoreConfig",
    "curriculum.apps.CurriculumConfig",
    "journal.apps.JournalConfig",
    "publications.apps.PublicationsConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "yourlifestory.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.site_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "yourlifestory.wsgi.application"

if env_flag("USE_SQLITE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env_required("POSTGRES_DB"),
            "USER": env_required("POSTGRES_USER"),
            "PASSWORD": env_required("POSTGRES_PASSWORD"),
            "HOST": env_required("POSTGRES_HOST"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = os.getenv("TIME_ZONE", "UTC")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/workspace/"
LOGOUT_REDIRECT_URL = "/feed/"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
