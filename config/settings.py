"""Configuración del Sistema de Seguimiento de Acuerdos (SSA).

Toda la configuración sensible se toma de variables de entorno (en Azure App Service:
Configuración > Variables de entorno; en local: archivo .env, ver .env.example).

Base de datos, por orden de prioridad:
  1. Microsoft SQL Server / Azure SQL  -> si existe MSSQL_HOST
  2. PostgreSQL                        -> si existe POSTGRES_HOST
  3. SQLite (solo desarrollo local)    -> en cualquier otro caso
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name, default=False):
    return os.environ.get(name, str(default)).lower() in ("1", "true", "yes", "si", "sí")


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-inseguro-cambiar-en-produccion")
DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = [h.strip() for h in os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000").split(",") if o.strip()]

# Azure App Service define WEBSITE_HOSTNAME (p. ej. acuerdos.azurewebsites.net): se admite automáticamente.
EN_AZURE = bool(os.environ.get("WEBSITE_HOSTNAME"))
if EN_AZURE:
    ALLOWED_HOSTS.append(os.environ["WEBSITE_HOSTNAME"])
    CSRF_TRUSTED_ORIGINS.append(f"https://{os.environ['WEBSITE_HOSTNAME']}")
    # Azure termina TLS en su balanceador y reenvía la petición por HTTP con este encabezado.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "seguimiento",
]
if os.environ.get("POSTGRES_HOST") and not os.environ.get("MSSQL_HOST"):
    INSTALLED_APPS.insert(-1, "django.contrib.postgres")  # lookup "unaccent" para búsquedas sin acentos

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
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
                "seguimiento.context.institucion_usuario",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

if os.environ.get("MSSQL_HOST"):
    # Microsoft SQL Server / Azure SQL Database mediante mssql-django y el ODBC Driver 18.
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "NAME": os.environ.get("MSSQL_DB", "acuerdos"),
            "USER": os.environ.get("MSSQL_USER", ""),
            "PASSWORD": os.environ.get("MSSQL_PASSWORD", ""),
            "HOST": os.environ["MSSQL_HOST"],  # p. ej. miservidor.database.windows.net
            "PORT": os.environ.get("MSSQL_PORT", "1433"),
            "CONN_MAX_AGE": 60,
            "CONN_HEALTH_CHECKS": True,
            "OPTIONS": {
                "driver": os.environ.get("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server"),
                # Tiempo de espera del inicio de sesión (s). Por defecto el driver espera solo 15 s, insuficiente
                # para despertar una base serverless en pausa.
                "connection_timeout": int(os.environ.get("MSSQL_LOGIN_TIMEOUT", "90")),
                # Azure SQL exige cifrado; el tiempo de espera amplio cubre el arranque de bases "serverless" en pausa.
                "extra_params": os.environ.get(
                    "MSSQL_EXTRA_PARAMS", "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=60"),
            },
        }
    }
elif os.environ.get("POSTGRES_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("POSTGRES_DB", "acuerdos"),
            "USER": os.environ.get("POSTGRES_USER", "acuerdos"),
            "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ.get("POSTGRES_PORT", "5432"),
            "CONN_MAX_AGE": 60,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT", BASE_DIR / "media"))

# Bitácora a la salida estándar: Azure la muestra en "Secuencia de registro" (Log stream).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"consola": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["consola"], "level": os.environ.get("DJANGO_LOG_LEVEL", "WARNING")},
}

LOGIN_URL = "login"

# Modo de prueba: cualquier usuario con sesión puede agregar y modificar datos (ver seguimiento/permisos.py).
MODO_PRUEBA = env_bool("DJANGO_MODO_PRUEBA", False)
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "seguimiento.permisos.PermisosModoPrueba",
]
LOGIN_REDIRECT_URL = "seguimiento:tablero"
LOGOUT_REDIRECT_URL = "login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
