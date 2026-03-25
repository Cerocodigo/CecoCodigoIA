# core/views/modules/validate_model_view.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from core.db.mongo.services.models.model_query_service import (
    ModelQueryService,
)

from core.services.modules.model_validator_service import (
    ModelValidatorService,
)


@require_POST
def validate_model_view(request, module_id: str):
    print("--- validate_model_view (module_id:", module_id, ") ---")
    """
    Endpoint de desarrollo:
    Valida el modelo Mongo usando ModelValidatorService
    """

    company = request.company_ctx

    if not company:
        return JsonResponse(
            {"success": False, "error": "Empresa no activa"},
            status=400,
        )

    try:
        # 1️⃣ Obtener modelo desde Mongo
        models = ModelQueryService.get_models_for_module(
            company=company,
            module_id=module_id,
            is_raw=True,
        )
        print("------------------------------------")
        print("Modelo obtenido para validación: Cantidad:")
        print(len(models)     )
        print("------------------------------------")

        if not models:
            return JsonResponse(
                {"success": False, "error": "Modelos no encontrados"},
                status=404,
            )

        # 2️⃣ Validar modelo
        result_for_model = {}
        for model in models:
            print("Modelo:", model["_id"], "Campos:", len(model.get("campos", [])))
            validation_result = ModelValidatorService.validate(model)
            result_for_model[model["_id"]] = validation_result


        return JsonResponse({
            "validate": True,
            "result": result_for_model,
        })

    except Exception as e:
        return JsonResponse(
            {"validate": False, "error": str(e)},
            status=500,
        )