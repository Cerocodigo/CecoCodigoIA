# core/context_processors.py
# =========================
# Context processors globales del sistema
# =========================

def app_context(request):
    """
    Inyecta contexto global disponible en TODOS los templates.

    Incluye:
    - Usuario autenticado
    - Empresa activa (si existe)
    - Relación usuario-empresa (si existe)

    Compatible con:
    - Dashboard
    - Onboarding
    - Vistas públicas
    """

    return {
        "current_user": getattr(request, "user_ctx", None),
        "current_company": getattr(request, "company_ctx", None),
        "current_user_company": getattr(request, "user_company_ctx", None),
    }