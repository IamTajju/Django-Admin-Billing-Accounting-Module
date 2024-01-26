from .base import *

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    default=secrets.token_urlsafe(nbytes=64),
)

DEBUG = True

ALLOWED_HOSTS = ["*"]


CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]

CORS_ALLOWED_ORIGINS = [
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8000',
]
