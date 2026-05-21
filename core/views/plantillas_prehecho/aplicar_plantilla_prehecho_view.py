# core/views/plantillas_prehecho/apply_plantilla_prehecho_view.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.db.sqlite.models.modelo_prehecho import (
    ModeloPrehecho,
)

from core.services.plantillas_prehecho.apply_prebuilt_template_service import (
    ApplyPrebuiltTemplateService,
)


@require_POST
def aplicar_plantilla_prehecho_view(
    request,
    plantilla_id,
):
    """
    Aplica una plantilla prehecha
    sobre la empresa actual.

    Recibe:
    - metadata dinámica
    - strategy (keep / clean)
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
    # Obtener strategy
    # =========================
    strategy = request.POST.get(
        "strategy",
        "keep",
    )

    if strategy not in ["keep","clean",]:
        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Estrategia inválida"
                ),
            },
            status=400,
        )

    # =========================
    # Aplicar plantilla
    # =========================
    try:
        result = ApplyPrebuiltTemplateService.apply(
            company=company,
            plantilla=plantilla,
            request_files=request.FILES,
            request_post=request.POST,
            strategy=strategy,
        )
    except Exception as e:

        return JsonResponse(
            {
                "success": False,
                "message": (
                    "Ocurrió un error "
                    "aplicando la plantilla"
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
            "message": (
                "Plantilla aplicada correctamente"
            ),
            "result": result,
        }
    )