from django.db import models
from django.utils import timezone


class User(models.Model):
    """
    Usuario base del sistema.
    Autenticación y datos principales.
    """

    # =========================
    # Datos de autenticación
    # =========================
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)

    # =========================
    # Datos personales
    # =========================
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    # =========================
    # Activación
    # =========================
    is_active = models.BooleanField(default=False)
    activation_code = models.CharField(max_length=128, null=True, blank=True)
    activation_expires = models.DateTimeField(null=True, blank=True)

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email
