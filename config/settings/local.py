from .base import *

DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

SITE_URL = "http://127.0.0.1:8000"

# =========================
# EMAIL (SMTP REAL - GMAIL)
# =========================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = "smtp.ipage.com"
EMAIL_PORT = 465

EMAIL_USE_TLS = False
EMAIL_USE_SSL = True

EMAIL_HOST_USER = "documentos@cerocodigo.com"
EMAIL_HOST_PASSWORD = "@Dmin1992nlubkov"

DEFAULT_FROM_EMAIL = "documentos@cerocodigo.com"