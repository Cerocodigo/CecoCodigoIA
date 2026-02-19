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

    company = request.company_ctx

    #? =========================
    #? Sincronización Mongo → MySQL (Desarrollo)
    #? =========================
    UpdateModelMySQLSchemaService.update_schema_for_model(
            company=company,
            model_id=module_id,
        )


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
    # Datos MySQL del módulo
    # =========================
    columns, rows, field_metadata = ModuleTableDataService.get_table_data(
        company=company,
        model_definition=models[0],
        limit=1000,
    )

    print("--------------------------------")
    print("field_metadata")
    for meta in field_metadata:
        print(meta+": ", field_metadata[meta])
        print("--------------------------------")
    print("--------------------------------")


    # =========================
    # Contexto
    # =========================
    context = {
        "user": user,
        "company": company,
        "module": module,
        "models": models,
        "columns": columns,
        "rows": rows,
        "field_metadata": field_metadata,
    }
    return render(
        request,
        "core/modules/module_main.html",
        context,
    )
