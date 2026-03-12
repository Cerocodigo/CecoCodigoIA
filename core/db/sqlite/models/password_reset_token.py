# core/db/sqlite/models/password_reset_token.py

from django.db import models
from django.utils import timezone

from core.db.sqlite.models.user import User


class PasswordResetToken(models.Model):
    """
    Token de recuperación de contraseña.
    Un solo uso, con expiración.
    """

    # =========================
    # Relaciones
    # =========================
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="password_reset_tokens"
    )

    # =========================
    # Token
    # =========================
    token = models.CharField(max_length=128, unique=True)

    # =========================
    # Control de estado
    # =========================
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "password_reset_token"
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["expires_at"]),
        ]

    def is_expired(self) -> bool:
        """
        Indica si el token ya expiró.
        """
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"PasswordResetToken(user={self.user.email}, used={self.used})"
