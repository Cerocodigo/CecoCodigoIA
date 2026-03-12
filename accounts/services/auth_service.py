# accounts/services/auth_service.py

from django.contrib.auth.hashers import check_password
from core.db.sqlite.models.user import User


def authenticate_user(email: str, password: str):
    """
    Autentica credenciales contra SQLite.

    Retorna:
    - None        → credenciales inválidas
    - "INACTIVE"  → credenciales válidas pero usuario inactivo
    - User        → login válido
    """

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return None

    # =========================
    # Validar password (hash)
    # =========================
    if not check_password(password, user.password_hash):
        return None

    # =========================
    # Validar estado
    # =========================
    if not user.is_active:
        return "INACTIVE"

    return user
