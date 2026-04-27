# core/views/modules/module_main_view.py
# =====================================
# Vista principal de un módulo
# =====================================

from django.shortcuts import render, redirect
from django.http import Http404

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany

from core.db.mongo.services.modules.module_query_service import (ModuleQueryService,)
from core.db.mongo.services.models.model_query_service import (ModelQueryService,)

from core.services.modules.module_table_data_service import (ModuleTableDataService,)

from core.db.mongo.services.reports.report_query_service import (ReportQueryService,)

from core.services.ui.message_service import set_view_msg, pop_view_msg

# Servicio de sincronización de esquema MySQL (Solo si es necesario)
from core.services.modules.ensure_model_schema_service import (EnsureModelSchemaService,)

def module_main_view(request, module_id: str):
    """
    Vista principal del módulo:
    /modulo/<module_id>/main/
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
    # Obtener módulo (Mongo)
    # =========================
    module = ModuleQueryService.get_module_by_id(
        company=company,
        module_id=module_id,
    )

    if not module:
        raise Http404("Módulo no encontrado")

    # =========================
    # Obtener modelos del módulo (Mongo)
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=module_id,
    )

    # =========================
    # Validación adicional: Si no hay modelos, mostrar mensaje en UI
    # =========================
    if not models:
        set_view_msg(request, "warning", "Este módulo no tiene modelos definidos. Por favor, crea un modelo para empezar.")
        return render(
            request,
            "core/modules/module_main.html",
            {
                "module": module,
                "models": [],
                "columns": [],
                "rows": [],
                "field_metadata": {},
                "reports": [],
                "view_msg": pop_view_msg(request),
            }
        )
    
    # =========================
    # Sincronizar esquema MySQL del modelo principal (Solo si es necesario)
    # =========================
    ensure_result = EnsureModelSchemaService.ensure_model_schema(
        company=company,
        models=models,
    )

    # =========================
    # Si alguna sincronización falla, mostrar mensaje de error
    # pero intentar cargar la vista con los datos disponibles
    # =========================
    if not ensure_result["success"]:

        failed_models = [
            item
            for item in ensure_result.get("results", [])
            if not item.get("success", False)
        ]

        error_details = []

        for item in failed_models:
            table_name = item.get("table", "sin_tabla")
            errors = item.get("errors", [])

            if errors:
                safe_errors = [str(error) for error in errors]

                error_details.append(
                    f"{table_name}: {', '.join(safe_errors)}"
                )
            else:
                error_details.append(
                    f"{table_name}: error desconocido"
                )

        set_view_msg(
            request,
            "error",
            "Error sincronizando algunos modelos del módulo. "
            + "Detalles: "
            + " | ".join(error_details)
            + ". Se intentará cargar los datos, pero podrían no mostrarse correctamente."
        )

        return render(
            request,
            "core/modules/module_main.html",
            {
                "module": module,
                "models": models,
                "columns": [],
                "rows": [],
                "field_metadata": {},
                "reports": [],
                "view_msg": pop_view_msg(request),
            }
        )


    # =========================
    # Datos MySQL del módulo
    # =========================
    columns, rows, field_metadata = ModuleTableDataService.get_table_data(
        company=company,
        model_definition=models[0],
        limit=1000,
    )

    # =========================
    # Obtener reportes del módulo (Mongo)
    # =========================
    reports = ReportQueryService.get_reports_by_module(
        company=company,
        module_id=module_id,
    )

    # =========================
    # Obtener mensaje flash
    # =========================
    view_msg = pop_view_msg(request)

    # =========================
    # Contexto
    # =========================
    context = {
        "module": module,
        "models": models,
        "columns": columns,
        "rows": rows,
        "field_metadata": field_metadata,
        "reports": reports,
        "view_msg": view_msg,
    }
    return render(
        request,
        "core/modules/module_main.html",
        context,
    )
