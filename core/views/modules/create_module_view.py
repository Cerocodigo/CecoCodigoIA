import json

from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.http import Http404


from core.db.mongo.services.modules.module_query_service import (ModuleQueryService)
from core.db.mongo.services.models.model_query_service import (ModelQueryService)
from core.services.modules.update_model_mysql_schema_service import (UpdateModelMySQLSchemaService,)

@require_POST
@csrf_protect
def create_module_view(request):
    """
    Crea un nuevo módulo en la colección 'modulos' de MongoDB.

    Espera un POST JSON con:
        - nombre
        - descripcion
        - uso (alta | media | baja)
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
    # Parseo JSON
    # =========================
    try:
        data = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return JsonResponse(
            {"error": "JSON inválido"},
            status=400
        )

    nombre = data.get("nombre", "").strip()
    descripcion = data.get("descripcion", "").strip()
    uso = data.get("uso", "").strip().lower()

    # =========================
    # Validaciones
    # =========================
    if not nombre:
        return JsonResponse(
            {"error": "El nombre del módulo es obligatorio"},
            status=400
        )

    if uso not in ["alto", "medio", "bajo"]:
        return JsonResponse(
            {"error": "El uso debe ser: alto, medio o bajo"},
            status=400
        )

    # =========================
    # Creación del módulo y modelo en MongoDB
    # =========================
    try:
        # Creación del módulo
        module = ModuleQueryService.create_module(
            company=company,
            nombre=nombre,
            descripcion=descripcion,
            uso=uso,
        )
        # Creación del modelo asociado al módulo
        model = ModelQueryService.create_model(
            company=company,
            module_id=module["_id"],
            nombre=nombre,
        )
        # Sincronización del esquema MySQL para el nuevo modelo
        UpdateModelMySQLSchemaService.update_schema_for_model(
            company=company,
            model_id=model["_id"],
        )

    except ValueError as e:
        return JsonResponse(
            {"error": str(e)},
            status=400
        )
    except Exception:
        return JsonResponse(
            {"error": "Error interno al crear el módulo"},
            status=500
        )

    # =========================
    # Respuesta OK
    # =========================
    return JsonResponse(
        {
            "success": True,
            "module": {
                "id": module["_id"],
                "nombre": module["nombre"],
                "descripcion": module["descripcion"],
                "uso": module["uso"],
                "activo": module["activo"],
            },
            "model": {
                "id": model["_id"],
                "tabla": model["tabla"],
                "pk": model["pk"],
                "campos": model["campos"],
                "activo": model["activo"],
            }
        },
        status=201
    )



