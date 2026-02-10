# core/db/mysql/services/module_data_query_service.py
# ==================================================
# Servicio MySQL para obtención de datos de módulos
# ==================================================

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService
from core.db.mysql.sql.sql_generator import SQLGenerator


class ModuleDataQueryService:
    """
    Servicio encargado de obtener datos operativos
    de un módulo desde MySQL.
    """

    @staticmethod
    def get_placeholder_data():
        """
        Datos temporales para UI cuando aún no hay tabla.
        Retorna:
            ([column_names], [rows])
        """

        column_names = [
            "ColumnaA",
            "ColumnaB",
            "ColumnaC",
            "ColumnaD",
        ]

        rows = [
            ["Dato A1", "Dato B1", "Dato C1", "Dato D1"],
            ["Dato A2", "Dato B2", "Dato C2", "Dato D2"],
            ["Dato A3", "Dato B3", "Dato C3", "Dato D3"],
        ]

        return column_names, rows

    @staticmethod
    def fetch_table_data(*, company, table_name: str, campos: list[dict]):
        """
        Obtiene datos reales desde MySQL usando
        infraestructura oficial.

        `campos` viene desde MongoDB.
        """

        # =========================
        # 1️⃣ Extraer nombres SQL
        # =========================
        if not campos:
            return [], []

        column_names = [campo["nombre"] for campo in campos]

        # =========================
        # 2️⃣ Infraestructura MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        # =========================
        # 3️⃣ Generar SELECT
        # =========================
        sql, params = SQLGenerator.select(
            table_name=table_name,
            columns=column_names,
        )

        # =========================
        # 4️⃣ Ejecutar estructurado
        # =========================
        return dml.fetch_all_structured(sql, params)
