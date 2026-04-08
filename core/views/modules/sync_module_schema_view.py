# core/views/modules/sync_module_schema_view.py

from django.http import JsonResponse, Http404
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from core.db.sqlite.models.user import User

from core.db.mongo.services.modules.module_query_service import (
    ModuleQueryService,
)

from core.db.mongo.services.models.model_query_service import (
    ModelQueryService,
)

from core.services.modules.model_sync_orchestrator_service import (
    ModelSyncOrchestratorService,
)

from core.services.modules.update_model_mysql_schema_service import (
    UpdateModelMySQLSchemaService,
)


@require_POST
def sync_module_schema_view(request, module_id: str):
    """
    Endpoint de validación + sincronización de esquema por módulo.

    NUEVO FLUJO:

    1. Validar TODOS los modelos
    2. Corregir si aplica
    3. Re-validar todos
    4. SOLO SI TODOS son válidos → sincronizar MySQL

    Garantiza:
    - Consistencia total del módulo
    - No aplicar cambios parciales
    """

    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    # =========================
    # Empresa activa
    # =========================
    company = getattr(request, "company_ctx", None)

    if not company:
        return JsonResponse(
            {"success": False, "error": "Empresa no activa"},
            status=400,
        )

    try:
        # =========================
        # 1. Obtener módulo
        # =========================
        module = ModuleQueryService.get_module_by_id(
            company=company,
            module_id=module_id,
        )

        if not module:
            raise Http404("Módulo no encontrado")

        # =========================
        # 2. Obtener modelos del módulo
        # =========================
        models = ModelQueryService.get_models_for_module(
            company=company,
            module_id=module_id,
            is_raw=True,
        )

        if not models:
            return JsonResponse(
                {
                    "success": False,
                    "error": "El módulo no tiene modelos asociados",
                },
                status=400,
            )

        # =========================
        # 3. Ordenar modelos (cabecera → detalle)
        # =========================
        models_sorted = sorted(
            models,
            key=lambda m: 0 if m.get("rol") == "cabecera" else 1
        )

        # =========================
        # 4. PROCESAR MODELOS (SIN SYNC)
        # =========================
        results = []
        all_success = True
  
        for model in models_sorted:
            model_id = model.get("_id") or model.get("id")
            rol = model.get("rol")

            try:
                result = ModelSyncOrchestratorService.process_model(model)

                results.append({
                    "model": model_id,
                    "rol": rol,
                    "success": result["success"],
                    "stage": result.get("stage"),
                    "errors": result.get("errors", []),
                    "changes": result.get("changes", []),
                    "final_model": result.get("final_model"),
                })
                if not result["success"]:
                    all_success = False

            except Exception as e:
                all_success = False

                results.append({
                    "model": model_id,
                    "rol": rol,
                    "success": False,
                    "stage": "exception",
                    "errors": [
                        {
                            "tipoError": "Error inesperado",
                            "ubicacion": "orchestrator",
                            "elemento": str(e),
                            "sugerenciaCorreccion": "Revisar logs del servidor",
                        }
                    ],
                })

        # =========================
        # 5. SYNC SOLO SI TODO OK
        # =========================
        sync_summary = []

        if all_success:
            for result in results:
                model_id_origen = result["model"]
                processed_model = result.get("final_model")

                try:
                    sync_result = UpdateModelMySQLSchemaService.sync_schema_for_model(
                        model=processed_model,
                        company=company,
                    )

                    if sync_result.get("synchronization_executed") is True:
                        sync_mongo_result = ModelQueryService.replace_model(
                            company=company,
                            old_model_id=model_id_origen,
                            new_model=processed_model,
                        )

                    sync_summary.append({
                        "model": model.get("_id"),
                        "success": True,
                        "sync_result": sync_result,
                    })

                except Exception as e:
                    all_success = False

                    sync_summary.append({
                        "model": model.get("_id"),
                        "success": False,
                        "error": str(e),
                    })

        # =========================
        # 6. RESPUESTA FINAL
        # =========================
        return JsonResponse(
            {
                "success": all_success,
                "module_id": module_id,
                "total_models": len(models_sorted),
                "results": results,
                "sync_executed": all_success,
                "sync_summary": sync_summary if all_success else [],
            },
            status=200 if all_success else 207,
        )

    except Http404 as e:
        return JsonResponse(
            {"success": False, "error": str(e)},
            status=404,
        )

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "stage": "server",
                "errors": [
                    {
                        "tipoError": "Error interno",
                        "ubicacion": "endpoint",
                        "elemento": str(e),
                        "sugerenciaCorreccion": "Revisa logs del servidor",
                    }
                ],
            },
            status=500,
        )