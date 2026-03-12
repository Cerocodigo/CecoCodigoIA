from django.shortcuts import render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from datetime import timedelta
import secrets

from core.db.sqlite.models.user import User


def register_user_view(request):

    if request.method == "POST":
        email = request.POST.get("email", "").lower().strip()
        password = request.POST.get("password", "").strip()
        password_confirm = request.POST.get("password_confirm", "").strip()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        # =========================
        # Validaciones básicas
        # =========================
        if not all([email, password, password_confirm, first_name, last_name]):
            messages.error(request, "Todos los campos son obligatorios")
            return render(request, "accounts/register_user.html")

        if password != password_confirm:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "accounts/register_user.html")

        # =========================
        # Buscar usuario existente
        # =========================
        user = User.objects.filter(email=email).first()

        activation_code = secrets.token_urlsafe(32)
        activation_expires = timezone.now() + timedelta(hours=24)

        if user:
            if user.is_active:
                messages.error(request, "Este correo ya está registrado y activo")
                return render(request, "accounts/register_user.html")

            # Usuario existe pero NO está activo → regenerar activación
            user.activation_code = activation_code
            user.activation_expires = activation_expires
            user.save(update_fields=["activation_code", "activation_expires", "updated_at"])

        else:
            # Crear usuario nuevo
            User.objects.create(
                email=email,
                password_hash=make_password(password),
                first_name=first_name,
                last_name=last_name,
                is_active=False,
                activation_code=activation_code,
                activation_expires=activation_expires,
            )

        # =========================
        # Enviar correo de activación
        # =========================
        activation_link = f"{settings.SITE_URL}/register/activate/{activation_code}"

        send_mail(
            subject="Activa tu cuenta - CeCoCódigo",
            message=(
                f"Hola {first_name},\n\n"
                f"Para activar tu cuenta, usa el siguiente enlace:\n\n"
                f"{activation_link}\n\n"
                f"Este enlace expira en 24 horas."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        return render(request, "accounts/register_check_email.html")

    return render(request, "accounts/register_user.html")
