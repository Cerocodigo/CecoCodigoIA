from django.shortcuts import render, redirect
from django.http import Http404


def iniciar_ia_view(request):
    # =========================
    # Usuario, empresa y relación usuario-empresa del contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")

    # =========================
    # Aquí iría la lógica para iniciar el flujo de IA, por ahora es un placeholder
    # =========================

    # =========================
    # Render temporal habría que renderizar un nuevo template específico para este flujo, por ahora reutilizamos el dashboard con un mensaje
    # =========================
    context = {
        "modulos": [],
        "pending_join_requests": [],
        "has_modules": False,
    }
    return render(request, "core/dashboard.html", context)