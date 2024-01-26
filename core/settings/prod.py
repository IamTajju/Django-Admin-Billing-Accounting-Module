from .base import *

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    default=secrets.token_urlsafe(nbytes=64),
)

DEBUG = False

ALLOWED_HOSTS = ["billing.odysseydev.net",
                 "tahzeebahmed.com", "billing.tahzeebahmed.com"]

CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True

CONN_MAX_AGE = None

CSRF_TRUSTED_ORIGINS = [
    'https://billing.odysseydev.net',
    'https://billing.tahzeebahmed.com'
]

CORS_ALLOWED_ORIGINS = [
    'https://billing.odysseydev.net',
    'https://billing.tahzeebahmed.com'
]
