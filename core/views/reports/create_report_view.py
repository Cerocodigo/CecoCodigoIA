# core/views/reports/create_report_view.py
# ==================================================
# Vista de creación de Reportes dinámicos vía IA
# ==================================================

import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from core.services.reports.report_ai_service import (
    ReportAIService,
)
from core.services.reports.report_persistence_service import (
    ReportPersistenceService,
)


@require_POST
@csrf_protect
def create_report_view(request):
    """
    Crea un nuevo reporte dinámico mediante IA.

    Espera un POST JSON con:
        - prompt (string)

    Flujo:
        1️⃣ Valida request
        2️⃣ Genera definición IA
        3️⃣ Persiste reporte validado
        4️⃣ Devuelve resultado
    """

    # =========================
    # Empresa activa
    # =========================
    company = getattr(request, "company_ctx", None)

    if not company:
        return JsonResponse(
            {"error": "Empresa no encontrada en el contexto"},
            status=400
        )

    # =========================
    # Parseo JSON
    # =========================
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "JSON inválido"},
            status=400
        )

    user_prompt = data.get("prompt", "").strip()
    if not user_prompt:
        return JsonResponse(
            {"error": "El campo 'prompt' es obligatorio"},
            status=400
        )

    # =========================
    # Generación IA
    # =========================
    try:
        result = ReportAIService.generate_report_definition(
            company=company,
            user_prompt=user_prompt,
        )
    except Exception:
        return JsonResponse(
            {"error": "Error interno al generar el reporte"},
            status=500
        )

    if not result["success"]:
        return JsonResponse(
            {
                "error": "No fue posible generar un reporte válido",
                "details": result["errors"],
            },
            status=400
        )

    report_definition = result["report_definition"]

    # =========================
    # Persistencia
    # =========================
    try:
        document = ReportPersistenceService.create_report(
            company=company,
            report_definition=report_definition,
            created_by=request.user_ctx.id,
        )
    except Exception:
        return JsonResponse(
            {"error": "Error interno al guardar el reporte"},
            status=500
        )

    # =========================
    # Respuesta OK
    # =========================
    return JsonResponse(
        {
            "success": True,
            "report": {
                "id": document["_id"],
                "nombre": document["nombre"],
                "descripcion": document["descripcion"],
                "modulos": document["modulos"],
                "exportable": document["exportable"],
                "version": document["version"],
                "activo": document["activo"],
            }
        },
        status=201
    )