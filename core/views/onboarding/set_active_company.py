from django.shortcuts import redirect
from django.contrib import messages

from core.db.sqlite.models.user_company import UserCompany


def set_active_company_view(request, company_id):
    print("set_active_company_view called with company_id:", company_id)
    user = request.user_ctx

    # Validar que el usuario pertenece a la empresa
    userCompanyActive = UserCompany.objects.filter(
        user=user,
        company_id=company_id,
        is_active=True
    ).first()

    if not userCompanyActive:
        messages.error(request, "No tienes acceso a esta empresa")
        return redirect("core:select_company")

    # Setear empresa activa
    request.session["company_id"] = company_id

    return redirect("core:dashboard")