from django.shortcuts import render, redirect
from django.contrib import messages

from core.services.password_reset_service import PasswordResetService


def password_reset_confirm_view(request, token: str):
    """
    Confirmación de recuperación de contraseña.
    """

    # =========================
    # Validar token (GET y POST)
    # =========================
    reset_token = PasswordResetService.validate_token(token)

    if not reset_token:
        messages.error(
            request,
            "El enlace de recuperación no es válido o ha expirado"
        )
        return redirect("accounts:login")

    user = reset_token.user

    # =========================
    # POST
    # =========================
    if request.method == "POST":
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()

        if not password or not password_confirm:
            messages.error(request, "Debes completar ambos campos")
            return render(
                request,
                "accounts/password_reset_confirm.html",
                {"email": user.email}
            )

        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden")
            return render(
                request,
                "accounts/password_reset_confirm.html",
                {"email": user.email}
            )

        # =========================
        # Reset vía servicio
        # =========================
        success = PasswordResetService.reset_password(
            token=token,
            new_password=password
        )

        if not success:
            messages.error(
                request,
                "El enlace ya fue usado o expiró"
            )
            return redirect("accounts:login")

        messages.success(
            request,
            "Tu contraseña fue actualizada correctamente. Ya puedes iniciar sesión."
        )
        return redirect("accounts:login")

    # =========================
    # GET
    # =========================
    return render(
        request,
        "accounts/password_reset_confirm.html",
        {"email": user.email}
    )
