# core/views/plantillas_prehecho/obtener_analisis_plantilla_view.py

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.db.sqlite.models.modelo_prehecho import (ModeloPrehecho)

from core.services.plantillas_prehecho.template_mysql_analysis_service import (
    TemplateMySQLAnalysisService,
)


@require_GET
def obtener_analisis_plantilla_view(
    request,
    plantilla_id,
):
    """
    Endpoint encargado de analizar
    el impacto de aplicar una plantilla
    prehecha sobre la empresa actual.
    """

    # =========================
    # Contexto requerido
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:

        return JsonResponse(
            {
                "success": False,
                "message": "Contexto inválido",
            },
            status=400,
        )

    # =========================
    # Obtener plantilla
    # =========================
    try:
        plantilla = ModeloPrehecho.objects.get(
            id=plantilla_id,
            activo=True,
        )

    except ModeloPrehecho.DoesNotExist:
        return JsonResponse(
            {
                "success": False,
                "message": "Plantilla no encontrada",
            },
            status=404,
        )

    # =========================
    # Analizar impacto
    # =========================
    try:
        analysis = TemplateMySQLAnalysisService.analyze_template_application(
            company=company,
            plantilla=plantilla,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Ocurrió un error "
                    "analizando la plantilla"
                ),
                "error": str(e),
            },
            status=500,
        )

    # =========================
    # Respuesta final
    # =========================
    return JsonResponse(
        {
            "success": True,
            "analysis": analysis,
        }
    )