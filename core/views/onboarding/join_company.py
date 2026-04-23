from django.shortcuts import redirect, render
from django.contrib import messages
from django.core.exceptions import ValidationError

from core.db.sqlite.services.join_company_service import JoinCompanyService


def join_company(request, token: str):
    """
    Vista para unirse a una empresa mediante token de invitación.
    """

    try:
        result = JoinCompanyService.join_company_by_token(
            user=request.user,
            token=token
        )

    except ValidationError as e:
        messages.error(request, str(e))
        return redirect("core:onboarding:select_company")

    # =========================
    # Caso: requiere aprobación
    # =========================
    if result["requires_approval"]:
        messages.info(
            request,
            "Tu solicitud fue enviada. "
            "El propietario de la empresa debe aprobar tu ingreso."
        )
        return redirect("core:onboarding:select_company")

    # =========================
    # Caso: ingreso exitoso
    # =========================
    messages.success(
        request,
        f"Te has unido correctamente a la empresa "
        f"{result['company'].nombre_comercial}"
    )

    return redirect("core:onboarding:select_company")
