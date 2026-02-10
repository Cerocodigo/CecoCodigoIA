from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone

from core.db.sqlite.models.user import User


def activate_account_view(request, activation_code):
    """
    Activa la cuenta del usuario usando el código enviado por correo.
    """

    user = User.objects.filter(
        activation_code=activation_code
    ).first()
    
    # =========================
    # Código inválido o ya usado
    # =========================
    if not user:
        messages.error(
            request,
            "El enlace de activación no es válido o ya fue utilizado."
        )
        return redirect("accounts:login")

    # =========================
    # Ya activo
    # =========================
    if user.is_active:
        messages.info(
            request,
            "Tu cuenta ya se encuentra activa. Puedes iniciar sesión."
        )
        return redirect("accounts:login")

    # =========================
    # Código expirado
    # =========================
    if not user.activation_expires or user.activation_expires < timezone.now():
        messages.error(
            request,
            "El enlace de activación ha expirado. Solicita uno nuevo."
        )
        return redirect("accounts:login")

    # =========================
    # Activar cuenta
    # =========================
    user.is_active = True
    user.activation_code = None
    user.activation_expires = None
    user.save(update_fields=[
        "is_active",
        "activation_code",
        "activation_expires",
        "updated_at"
    ])

    messages.success(
        request,
        "Cuenta activada correctamente. Ya puedes iniciar sesión."
    )

    return redirect("accounts:login")
