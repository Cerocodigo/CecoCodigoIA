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

    # ==================================================
    # Construcción ordenada de columnas según estándar
    # ==================================================

    @staticmethod
    def build_ordered_column_list(campos: list[dict]) -> list[str]:
        """
        Construye lista de columnas SQL considerando:

        - Siempre incluir id_*
        - Solo incluir visible=True (excepto id)
        - Ordenar primero area="main"
        - Luego area="side"
        - Orden ascendente por campo["orden"]
        """

        if not campos:
            return []

        main_fields = []
        side_fields = []
        id_field = None

        for campo in campos:
            nombre = campo.get("nombre")
            area = campo.get("area")
            visible = campo.get("visible", True)
            orden = campo.get("orden", 0)

            if nombre.lower().startswith("id_"):
                id_field = nombre
                continue

            if not visible:
                continue

            if area == "main":
                main_fields.append((orden, nombre))
            elif area == "side":
                side_fields.append((orden, nombre))

        # Ordenar por orden ascendente
        main_fields.sort(key=lambda x: x[0])
        side_fields.sort(key=lambda x: x[0])

        ordered_columns = []

        # Siempre primero el ID si existe
        if id_field:
            ordered_columns.append(id_field)

        # Luego main
        ordered_columns.extend([nombre for _, nombre in main_fields])

        # Luego side
        ordered_columns.extend([nombre for _, nombre in side_fields])

        return ordered_columns

    # ==================================================
    # Obtención principal
    # ==================================================

    @staticmethod
    def fetch_table_data(*, company, table_name: str, campos: list[dict], limit: int = 1000):
        """
        Obtiene datos reales desde MySQL usando
        infraestructura oficial.
        """

        if not campos:
            return [], []

        # =========================
        # 1️⃣ Construcción ordenada
        # =========================
        column_names = ModuleDataQueryService.build_ordered_column_list(campos)

        if not column_names:
            return [], []

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
        return dml.fetch_all_structured(
            sql + f" LIMIT {limit}",
            params
        )
