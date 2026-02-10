from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    # dominio producción
]

SITE_URL = ""

# =========================
# EMAIL (SMTP REAL - GMAIL)
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.ipage.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
