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

from core.services.ui.message_service import set_view_msg, pop_view_msg

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
    ##* antes se hacía la sincronización aquí, pero ahora se hace en un proceso separado (ver services/modules/update_model_mysql_schema_service.py)
    ##* Debería validarse si existe la tabla mysql, para sincronizarla, y recién ahí traer la data, si existe.
    

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
