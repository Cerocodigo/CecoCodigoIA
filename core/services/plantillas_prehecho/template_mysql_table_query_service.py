# core/services/plantillas_prehecho/template_mysql_table_query_service.py

from core.db.mysql.services.connection_service import (MySQLCompanyConnectionService)
from core.db.mysql.executor import (MySQLExecutor)
from core.db.mysql.services.dml_service import (MySQLDMLService)

class TemplateMySQLTableQueryService:
    """
    Servicio encargado de consultar
    tablas reales existentes en MySQL
    y sus cantidades de registros.
    """

    # =========================
    # Obtener tablas existentes
    # =========================
    @staticmethod
    def get_existing_tables(
        *,
        company,
    ):
        """
        Retorna nombres de tablas
        existentes en la base actual.
        """

        connection =  MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        try:
            executor = MySQLExecutor(connection)
            dml = MySQLDMLService(executor)

            sql = """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                ORDER BY table_name
            """

            rows = dml.fetch_all(sql)

            return [
                row["table_name"]
                for row in rows
            ]
        finally:
            try:
                connection.close()
            except Exception:
                pass

    # =========================
    # Contar registros tabla
    # =========================
    @staticmethod
    def count_records_for_table(
        *,
        company,
        table_name: str,
    ):
        """
        Cuenta registros
        de una tabla específica.
        """

        connection =  MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        try:
            executor = MySQLExecutor(connection)
            dml = MySQLDMLService(executor)

            sql = f"""
                SELECT COUNT(*) AS total
                FROM `{table_name}`
            """

            result = dml.fetch_one(sql)

            return result["total"]

        finally:
            try:
                connection.close()
            except Exception:
                pass

    # =========================
    # Obtener tablas + registros
    # =========================
    @staticmethod
    def get_tables_with_counts(
        *,
        company,
    ):
        """
        Retorna listado completo
        de tablas con cantidades
        de registros.
        """

        tables = TemplateMySQLTableQueryService.get_existing_tables(
            company=company
        )
        
        results = []

        for table_name in tables:
            total = TemplateMySQLTableQueryService.count_records_for_table(
                company=company,
                table_name=table_name,
            )
            

            results.append(
                {
                    "table_name": table_name,
                    "record_count": total,
                }
            )

        return results