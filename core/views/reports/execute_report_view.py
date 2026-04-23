# core/views/reports/execute_report_view.py

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from core.services.reports.report_execution_service import (
    ReportExecutionService,
)


@require_POST
@csrf_protect
def execute_report_view(request, report_id: str):
    # =========================
    # Usuario, empresa y relación usuario-empresa del contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        return JsonResponse({"error": "unauthorized"}, status=401)

    try:
        data = json.loads(request.body.decode("utf-8")) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    parametros = data.get("parametros", {})
    nivel = data.get("nivel", 0)

    try:
        result = ReportExecutionService.execute_level(
            company=company,
            report_id=report_id,
            nivel=nivel,
            parametros=parametros,
        )
    except Exception as e:
        return JsonResponse(
            {"error": "Error interno al ejecutar el reporte"},
            status=500,
        )

    if not result["success"]:
        return JsonResponse(
            {"error": result["errors"]},
            status=400,
        )

    return JsonResponse(
        {
            "success": True,
            "nivel": nivel,
            "data": result["data"],
        },
        status=200,
    )