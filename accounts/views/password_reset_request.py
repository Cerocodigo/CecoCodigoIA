from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from core.db.sqlite.models.user import User
from core.services.password_reset_service import PasswordResetService


def password_reset_request_view(request):
    """
    Solicitud de recuperación de contraseña.
    """

    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()

        if not email:
            messages.error(request, "Debes ingresar un correo electrónico")
            return render(request, "accounts/password_reset_request.html")

        user = User.objects.filter(email=email, is_active=True).first()

        # ⚠️ Importante: NO revelamos si existe o no
        if user:
            reset_token = PasswordResetService.create_token_for_user(user)

            reset_link = (
                f"{settings.SITE_URL}/password-reset/confirm/"
                f"{reset_token.token}"
            )

            send_mail(
                subject="Recuperación de contraseña - CeCoCódigo",
                message=(
                    f"Hola {user.first_name},\n\n"
                    f"Solicitaste recuperar tu contraseña.\n\n"
                    f"Usa el siguiente enlace para crear una nueva:\n\n"
                    f"{reset_link}\n\n"
                    f"Este enlace es válido por 60 minutos.\n\n"
                    f"Si no solicitaste este cambio, ignora este correo."
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

        # Siempre mostramos la misma pantalla
        return render(request, "accounts/password_reset_check_email.html")

    return render(request, "accounts/password_reset_request.html")
