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


# Database (MySQL 8.4 LTS) ----------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": config("DB_NAME", default="hospital_db"),
        "USER": config("DB_USER", default="hms_user"),
        "PASSWORD": config("DB_PASSWORD", default=""),
        "HOST": config("DB_HOST", default="127.0.0.1"),
        "PORT": config("DB_PORT", default="3306"),
        "OPTIONS": {"charset": "utf8mb4"},
        # Store datetimes in Kigali time. Because the connection time zone then
        # matches TIME_ZONE, Django never wraps columns in CONVERT_TZ(), so
        # TruncMonth/__date work even when MySQL's time zone tables are not
        # loaded (see "Monthly charts come back empty" in the plan).
        "TIME_ZONE": "Africa/Kigali",
        "TEST": {"NAME": "test_hospital_db", "CHARSET": "utf8mb4"},
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
