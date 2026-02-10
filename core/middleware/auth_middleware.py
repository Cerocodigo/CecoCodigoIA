# core/middleware/auth_middleware.py
# ==================================
# Middleware de autenticación y empresa activa
# ==================================

from django.shortcuts import redirect

from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company
from core.db.sqlite.models.user_company import UserCompany


class AuthRequiredMiddleware:
    """
    Middleware central de seguridad y contexto.

    Garantiza:
    - Usuario autenticado (SQLite)
    - Empresa activa seleccionada
    - Relación usuario-empresa válida

    NO abre conexiones MySQL
    NO contiene lógica de negocio
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # =========================
        # Inicializar contexto
        # =========================
        request.user_ctx = None
        request.company_ctx = None
        request.permissions = []

        # =========================
        # Django Admin (permitir todo)
        # =========================
        if path.startswith("/admin"):
            return self.get_response(request)

        # =========================
        # Rutas públicas exactas
        # =========================
        public_exact = [
            "/",  # login
        ]

        # =========================
        # Prefijos públicos
        # =========================
        public_prefixes = [
            "/static/",
            "/media/",
            "/favicon.ico",
            "/register/",
            "/password-reset/",
        ]

        # =========================
        # Prefijos post-login SIN empresa
        # =========================
        post_login_prefixes = [
            "/logout/",
            "/select-company/",
            "/create-company/",
            "/join/",
        ]
        

        # =========================
        # Permitir rutas públicas
        # =========================
        if path in public_exact:
            return self.get_response(request)

        for prefix in public_prefixes:
            if path.startswith(prefix):
                return self.get_response(request)

        # =========================
        # Validar sesión base
        # =========================
        user_id = request.session.get("user_id")
        company_id = request.session.get("company_id")

        if not user_id:
            request.session.flush()
            return redirect("/")

        # =========================
        # Cargar usuario
        # =========================
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            request.session.flush()
            return redirect("/")

        request.user_ctx = user

        # =========================
        # Permitir rutas post-login SIN empresa
        # =========================
        for prefix in post_login_prefixes:
            if path.startswith(prefix):
                return self.get_response(request)

        # =========================
        # A partir de aquí: REQUIERE empresa
        # =========================
        if not company_id:
            return redirect("/select-company/")

        # =========================
        # Cargar empresa
        # =========================
        try:
            company = Company.objects.select_related("mysql_server").get(
                id=company_id,
                is_active=True
            )
        except Company.DoesNotExist:
            request.session.pop("company_id", None)
            return redirect("/select-company/")

        # =========================
        # Validar relación usuario-empresa
        # =========================
        if not UserCompany.objects.filter(
            user=user,
            company=company,
            is_active=True
        ).exists():
            request.session.pop("company_id", None)
            return redirect("/select-company/")

        # =========================
        # Validación mínima de entorno MySQL
        # (solo metadatos, NO conexión)
        # =========================
        if not company.mysql_server or not company.mysql_db_name:
            # Empresa aún no provisionada completamente
            # Se fuerza retorno al flujo de selección
            return redirect("/select-company/")

        # =========================
        # Inyectar contexto definitivo
        # =========================
        request.company_ctx = company

        return self.get_response(request)
