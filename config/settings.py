"""
Django settings for the Hospital Management System (HMS).

Owned by Member A. Secrets and machine-specific values are read from `.env`
with python-decouple; copy `.env.example` to `.env` before the first run.
"""

from pathlib import Path

from decouple import Csv, config
from django.contrib.messages import constants as messages

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())
# Hosted over HTTPS (e.g. https://<username>.pythonanywhere.com), list the full origin here.
CSRF_TRUSTED_ORIGINS = config("CSRF_TRUSTED_ORIGINS", default="", cast=Csv())
# True once the site is HTTPS-only (PythonAnywhere: Web tab -> Force HTTPS), so the
# session and CSRF cookies are never sent over plain HTTP.
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = config("HTTPS_ONLY", default=False, cast=bool)


# Applications -----------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    # Project apps (all seven are registered from day one).
    "accounts",
    "staff",
    "patients",
    "appointments",
    "pharmacy",
    "billing",
    "analytics",
]

AUTH_USER_MODEL = "accounts.User"  # set BEFORE the first migrate

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Django 5.1+: every view requires login unless marked @login_not_required.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.hospital",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database (SQLite: a single db.sqlite3 file, git-ignored) ----------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        # Store datetimes in Kigali time, so the raw values in the file match
        # what the app shows.
        "TIME_ZONE": "Africa/Kigali",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Authentication ----------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "analytics:dashboard"
LOGOUT_REDIRECT_URL = "accounts:login"


# Internationalisation (Rwanda) -------------------------------------------------

LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Africa/Kigali"
USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = False


# Static files --------------------------------------------------------------------

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"


# Messages -> Bootstrap alert classes ----------------------------------------------

MESSAGE_TAGS = {messages.ERROR: "danger"}


# Hospital identity (shown in the sidebar, footer and printed invoices) ------------

HOSPITAL = {
    "NAME": config("HOSPITAL_NAME", default="Ubuzima Referral Hospital"),
    "SHORT_NAME": config("HOSPITAL_SHORT_NAME", default="Ubuzima HMS"),
    "ADDRESS": config("HOSPITAL_ADDRESS", default="KG 7 Ave, Kacyiru, Gasabo District, Kigali, Rwanda"),
    "PHONE": config("HOSPITAL_PHONE", default="+250 788 300 400"),
    "EMAIL": config("HOSPITAL_EMAIL", default="info@ubuzima-hospital.rw"),
    "TIN": config("HOSPITAL_TIN", default="102345678"),
    "CURRENCY": "RWF",
}
