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

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")
    
    # =========================
    # Relación usuario-empresa
    # =========================
    user_company = UserCompany.objects.filter(
        user=user,
        company=request.company_ctx,
        is_active=True
    ).first()

    
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
                "user": user,
                "company": company,
                "user_role": user_company.role_slug if user_company else "user",
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
        model=models[0],
    )

    # =========================
    # Si la sincronización falla, se muestra un mensaje de error pero se intenta cargar la vista con los datos disponibles (si los hay).
    # =========================
    if not ensure_result["success"]:
        set_view_msg(request, "error", "Error sincronizando esquema MySQL del modelo principal. Detalles: " + ensure_result.get("error", "Desconocido") + ". Se intentará cargar los datos, pero podrían no mostrarse correctamente.")
        return render(
            request,
            "core/modules/module_main.html",
            {
                "user": user,
                "company": company,
                "user_role": user_company.role_slug if user_company else "user",
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
        "user": user,
        "company": company,
        "user_role": user_company.role_slug if user_company else "user",
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
