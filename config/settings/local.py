from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

SITE_URL = "http://127.0.0.1:8000"

# =========================
# EMAIL (SMTP REAL - GMAIL)
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False

EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ' '

DEFAULT_FROM_EMAIL = ""
