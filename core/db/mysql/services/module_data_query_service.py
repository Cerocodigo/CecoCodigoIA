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

from core.services.modules.constants import AREAS_ROL


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

        - Siempre incluir PK
        - Solo visible=True (excepto pk)
        - Orden EXACTO según AREAS_ROL
        - Orden interno por campo["orden"]
        """

        if not campos:
            return []

        from core.services.modules.constants import AREAS_ROL

        grouped = {}
        pk_field = None

        # Obtener orden de áreas para cabecera (rol principal de tabla)
        config = AREAS_ROL.get("cabecera")
        ordered_areas = config["areas_validas"]

        # Inicializar grupos respetando orden
        for area in ordered_areas:
            grouped[area] = []

        for campo in campos:
            nombre = campo.get("nombre")
            area = campo.get("area")
            visible = campo.get("visible", True)
            orden = campo.get("orden", 0)

            if campo.get("tipo_base") == "pk":
                pk_field = nombre
                continue

            if not visible:
                continue

            if area in grouped:
                grouped[area].append((orden, nombre))

        # Ordenar dentro de cada área
        for area in grouped:
            grouped[area].sort(key=lambda x: x[0])

        ordered_columns = []

        # PK siempre primero
        if pk_field:
            ordered_columns.append(pk_field)

        # 🔥 RESPETA EXACTAMENTE EL ORDEN DEL ARRAY
        for area in ordered_areas:
            ordered_columns.extend([nombre for _, nombre in grouped[area]])

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
