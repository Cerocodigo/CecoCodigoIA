# accounts/views/login.py

from django.shortcuts import render, redirect
from django.contrib import messages

from accounts.services.auth_service import authenticate_user
from core.db.sqlite.models.user_company import UserCompany


def login_view(request):
    """
    Login real contra SQLite.
    """

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate_user(email, password)

        if not user:
            messages.error(request, "Credenciales inválidas")
            return render(request, "accounts/login.html")

        if user == "INACTIVE":
            messages.warning(request, "Tu cuenta aún no está activada")
            return render(request, "accounts/login.html")

        # =========================
        # Guardar sesión base
        # =========================
        request.session["user_id"] = user.id
        request.session["user_email"] = user.email
        request.session["user_name"] = f"{user.first_name} {user.last_name}"

        # =========================
        # ¿Tiene empresas?
        # =========================
        user_companies = UserCompany.objects.filter(
            user=user,
            is_active=True
        )

        if not user_companies.exists():
            # Aún no pertenece a ninguna empresa
            return redirect("core:select_company")

        # =========================
        # Usar primera empresa activa (por ahora)
        # =========================
        user_company = user_companies.first()
        request.session["company_id"] = user_company.company.id

        return redirect("core:dashboard")

    return render(request, "accounts/login.html")
