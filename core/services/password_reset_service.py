# core/services/password_reset_service.py

from datetime import timedelta
import secrets

from django.utils import timezone
from django.contrib.auth.hashers import make_password

from core.db.sqlite.models.user import User
from core.db.sqlite.models.password_reset_token import PasswordResetToken


class PasswordResetService:
    """
    Servicio central para recuperación de contraseña.
    """

    TOKEN_EXPIRATION_MINUTES = 60

    # =========================
    # Generar token
    # =========================
    @staticmethod
    def create_token_for_user(user: User) -> PasswordResetToken:
        """
        Crea un token de recuperación para un usuario.
        Invalida tokens anteriores no usados.
        """

        # Invalida tokens previos
        PasswordResetToken.objects.filter(
            user=user,
            used=False
        ).update(used=True)

        token = secrets.token_urlsafe(32)
        expires_at = timezone.now() + timedelta(
            minutes=PasswordResetService.TOKEN_EXPIRATION_MINUTES
        )

        return PasswordResetToken.objects.create(
            user=user,
            token=token,
            expires_at=expires_at
        )

    # =========================
    # Validar token
    # =========================
    @staticmethod
    def validate_token(token: str) -> PasswordResetToken | None:
        """
        Valida un token:
        - existe
        - no usado
        - no expirado
        """

        reset_token = PasswordResetToken.objects.filter(
            token=token,
            used=False
        ).select_related("user").first()

        if not reset_token:
            return None

        if reset_token.is_expired():
            reset_token.used = True
            reset_token.save(update_fields=["used"])
            return None

        return reset_token

    # =========================
    # Aplicar cambio de contraseña
    # =========================
    @staticmethod
    def reset_password(token: str, new_password: str) -> bool:
        """
        Cambia la contraseña del usuario usando el token.
        """

        reset_token = PasswordResetService.validate_token(token)

        if not reset_token:
            return False

        user = reset_token.user

        user.password_hash = make_password(new_password)
        user.updated_at = timezone.now()
        user.save(update_fields=["password_hash", "updated_at"])

        reset_token.used = True
        reset_token.save(update_fields=["used"])

        return True
