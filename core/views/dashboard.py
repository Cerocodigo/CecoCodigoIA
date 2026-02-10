# core/views/dashboard.py

from django.shortcuts import render, redirect

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.services.company_join_request_query_service import (CompanyJoinRequestQueryService)

from core.db.mongo.services.modules.module_query_service import ModuleQueryService


def dashboard_view(request):
    # =========================
    # Usuario autenticado (SQLite)
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
    # Solicitudes pendientes
    # =========================
    pending_join_requests = (CompanyJoinRequestQueryService.get_pending_for_owner(user))

    # =========================
    # Módulos activos (MongoDB)
    # =========================
    modulos = ModuleQueryService.get_active_modules(request.company_ctx)

    # =========================
    # Relación usuario-empresa
    # =========================
    user_company = UserCompany.objects.filter(
        user=user,
        company=request.company_ctx,
        is_active=True
    ).first()


    # =========================
    # Renderizar dashboard    
    # =========================
    context = {
        "user": user,
        "company": request.company_ctx,
        "modulos": modulos,
        "pending_join_requests": pending_join_requests,
        "user_role": user_company.role_slug if user_company else "user"
    }

    return render(request, "core/dashboard.html", context)
