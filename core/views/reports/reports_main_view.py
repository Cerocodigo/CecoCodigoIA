# core/views/reports/reports_main_view.py
# ======================================
# Vista principal de ejecución de reportes dinámicos
# ======================================

from django.shortcuts import render, redirect
from django.http import Http404

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany

from core.db.mongo.services.reports.report_query_service import (
    ReportQueryService,
)
import json
from django.core.serializers.json import DjangoJSONEncoder


def reports_main_view(request, report_id: str):
    """
    /reports/<report_id>/main/
    """

    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")

    # =========================
    # Relación usuario-empresa
    # =========================
    user_company = UserCompany.objects.filter(
        user=user,
        company=company,
        is_active=True
    ).first()

    # =========================
    # Obtener reporte (Mongo)
    # =========================
    report = ReportQueryService.get_report_by_id(
        company=company,
        report_id=report_id,
    )

    if not report:
        raise Http404("Reporte no encontrado")

    # =========================
    # Contexto
    # =========================
    context = {
        "user": user,
        "company": company,
        "user_role": user_company.role_slug if user_company else "user",
        "report": report,
    }

    return render(
        request,
        "core/reports/report_main.html",
        context,
    )