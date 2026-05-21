# core/views/plantillas_prehecho/obtener_metadata_plantilla_view.py

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho

from core.services.plantillas_prehecho.metadata_validation_service import (
    MetadataValidationService,
)


@require_GET
def obtener_metadata_plantilla_view(request, plantilla_id):
    """
    Endpoint encargado de retornar
    la metadata dinámica asociada
    a una plantilla prehecha.
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
            status=400
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
            status=404
        )

    # =========================
    # Obtener ejecuciones activas
    # =========================
    ejecuciones = plantilla.ejecuciones.filter(
        activo=True
    ).order_by("id")

    # =========================
    # Consolidar metadata
    # =========================
    metadata_resultado = []

    for ejecucion in ejecuciones:

        data_variables_mongo = (
            ejecucion.data_variables_mongo
        )

        # =========================
        # None permitido
        # =========================
        if not data_variables_mongo:
            continue

        # =========================
        # Validar estructura
        # =========================
        try:

            MetadataValidationService.validate_structure(
                data_variables_mongo=data_variables_mongo
            )

        except Exception as e:

            return JsonResponse(
                {
                    "success": False,
                    "message": (
                        f"Metadata inválida en ejecución "
                        f"#{ejecucion.id}"
                    ),
                    "error": str(e),
                },
                status=400
            )

        # =========================
        # Acumular metadata
        # =========================
        metadata_resultado.extend(
            data_variables_mongo
        )

    # =========================
    # Respuesta final
    # =========================
    return JsonResponse(
        {
            "success": True,
            "metadata": metadata_resultado,
        }
    )