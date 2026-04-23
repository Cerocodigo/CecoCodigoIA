# core/views/onboarding/select_company.py

from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.exceptions import ValidationError

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.services.join_company_service import JoinCompanyService


def select_company_view(request):
    """
    Onboarding de empresa:
    - Usuario autenticado
    - Puede:
        - Ver empresas a las que pertenece
        - Unirse por token
        - Ir a crear empresa
    """

    # =========================
    # Usuario autenticado
    # =========================
    user = request.user_ctx

    # =========================
    # LIMPIAR empresa activa (clave)
    # =========================
    request.session.pop("company_id", None)


    # =========================
    # POST → Unirse por token
    # =========================
    if request.method == "POST":
        token = request.POST.get("company_token", "").strip()

        if not token:
            messages.error(request, "Debes ingresar el token de invitación")
        else:
            try:
                result = JoinCompanyService.join_company_by_token(
                    user=user,
                    token=token
                )

                # =========================
                # Requiere aprobación
                # =========================
                if result.get("requires_approval"):
                    messages.info(
                        request,
                        "Tu solicitud fue enviada y está pendiente de aprobación"
                    )
                    return redirect("core:select_company")

                # =========================
                # Join inmediato
                # =========================
                request.session["company_id"] = result["company"].id
                messages.success(
                    request,
                    "Te has unido a la empresa correctamente"
                )
                return redirect("core:dashboard")

            except ValidationError as e:
                messages.error(request, str(e))

    
    # =========================
    # Empresas vinculadas
    # =========================
    user_companies = (
        UserCompany.objects
        .select_related("company")
        .filter(user=user, is_active=True, company__is_active=True)
    )

    companies = []
    for uc in user_companies:
        company = uc.company
        companies.append({
            "id": company.id,
            "name": company.nombre_comercial,
            "logo_url": company.logo_url,
            "role": uc.role_slug,
            "is_owner": uc.is_owner,
        })
        
    # =========================
    # Render
    # =========================
    context = {
        "user": user,
        "companies": companies,
    }

    return render(
        request,
        "core/onboarding/select_company.html",
        context
    )
