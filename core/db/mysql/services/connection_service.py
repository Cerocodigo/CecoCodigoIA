# core/db/mysql/services/connection_service.py
# ===========================================
# Servicio de conexión MySQL por empresa
# ===========================================

from django.core.exceptions import ValidationError

from core.db.mysql.connection import MySQLConnectionFactory
from core.db.mysql.exceptions import (
    MySQLConnectionError,
    MySQLConfigurationError,
)
from core.db.sqlite.models.company import Company


class MySQLCompanyConnectionService:
    """
    Servicio encargado de obtener una conexión MySQL
    operativa para una empresa específica.
    """

    @staticmethod
    def get_connection_for_company(*, company: Company):

        # =========================
        # Validaciones de dominio
        # =========================
        if not company:
            raise ValidationError("Empresa no proporcionada")

        if not company.is_active:
            raise ValidationError("La empresa está inactiva")

        if not company.mysql_server:
            raise MySQLConfigurationError(
                "La empresa no tiene servidor MySQL asignado"
            )

        if not company.mysql_db_name:
            raise MySQLConfigurationError(
                "La empresa no tiene base MySQL definida"
            )

        if not company.mysql_db_user or not company.mysql_db_password:
            raise MySQLConfigurationError(
                "La empresa no tiene credenciales MySQL definidas"
            )

        mysql_server = company.mysql_server

        # =========================
        # Crear conexión MySQL
        # =========================
        try:
            return MySQLConnectionFactory.get_company_connection(
                host=mysql_server.host,
                port=mysql_server.port,
                db_name=company.mysql_db_name,
                db_user=company.mysql_db_user,
                db_password=company.mysql_db_password,
            )
        except Exception as e:
            raise MySQLConnectionError(
                f"No se pudo conectar a MySQL para la empresa {company.id}",
                original_exception=e,
            )

    @staticmethod
    def get_connection_for_company_id(*, company_id: int):
        """
        Variante de conveniencia: recibe company_id.
        """

        try:
            company = Company.objects.select_related("mysql_server").get(
                id=company_id,
                is_active=True
            )
        except Company.DoesNotExist:
            raise ValidationError("Empresa no encontrada o inactiva")

        return MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
