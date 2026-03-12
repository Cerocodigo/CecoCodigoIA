# core/views/modules/sync_module_schema_view.py

from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from core.services.modules.update_model_mysql_schema_service import (
    UpdateModelMySQLSchemaService,
)


@require_POST
def sync_module_schema_view(request, module_id: str):
    """
    Endpoint auxiliar de desarrollo.
    Sincroniza el esquema MySQL a partir del modelo Mongo.
    """

    company = request.company_ctx

    if not company:
        return JsonResponse(
            {"success": False, "error": "Empresa no activa"},
            status=400,
        )

    try:
        UpdateModelMySQLSchemaService.update_schema_for_model(
            company=company,
            model_id=module_id,
        )

        return JsonResponse({"success": True})

    except Exception as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=500,
        )
