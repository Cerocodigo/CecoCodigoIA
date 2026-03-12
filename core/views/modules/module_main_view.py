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

#? Servicio de sincronización Mongo → MySQL (Desarrollo)
from core.services.modules.update_model_mysql_schema_service import (UpdateModelMySQLSchemaService,)

from core.db.mongo.services.reports.report_query_service import (ReportQueryService,)

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

    for model in models:
            #? =========================
            #? Sincronización Mongo → MySQL (Desarrollo)
            #? =========================
            UpdateModelMySQLSchemaService.update_schema_for_model(
                    company=company,
                    model_id=model["id"],
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
    }
    return render(
        request,
        "core/modules/module_main.html",
        context,
    )
