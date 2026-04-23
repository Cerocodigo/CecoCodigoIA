# core/views/dashboard.py

from django.shortcuts import render, redirect

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.services.company_join_request_query_service import (CompanyJoinRequestQueryService)

from core.db.mongo.services.modules.module_query_service import ModuleQueryService

from django.http import Http404


def dashboard_view(request):
    # =========================
    # Usuario, empresa y relación usuario-empresa del contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")


    # =========================
    # Solicitudes pendientes
    # =========================
    pending_join_requests = (CompanyJoinRequestQueryService.get_pending_for_owner(user))

    # =========================
    # Módulos activos (MongoDB)
    # =========================
    modulos = ModuleQueryService.get_active_modules(company)




    # =========================
    # Renderizar dashboard    
    # =========================
    context = {
        "modulos": modulos,
        "pending_join_requests": pending_join_requests,
    }

    return render(request, "core/dashboard.html", context)
