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
	# Usuario, empresa y relación usuario-empresa del contexto
	# =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")

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
        "report": report,
    }

    return render(
        request,
        "core/reports/report_main.html",
        context,
    )