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
    company = getattr(request, "company_ctx", None)

    if not company:
        return JsonResponse(
            {"error": "Empresa no encontrada en el contexto"},
            status=400,
        )

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