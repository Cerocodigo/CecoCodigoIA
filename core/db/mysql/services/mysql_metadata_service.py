# core/db/mysql/services/mysql_metadata_service.py
# ==================================================
# Servicio de metadata estructural MySQL por empresa
# ==================================================

from core.db.mongo.services.models.model_query_service import (
    ModelQueryService,
)
from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService


class MySQLMetadataService:
    """
    Servicio responsable de obtener la estructura real
    de las tablas MySQL asociadas a los modelos activos
    definidos en MongoDB.

    NO ejecuta lógica de negocio.
    NO modifica datos.
    SOLO consulta INFORMATION_SCHEMA.
    """

    @staticmethod
    def get_schema_metadata(*, company) -> dict:
        """
        Retorna metadata estructural de todas las tablas
        asociadas a modelos activos.

        Formato:

        {
            "tabla_clientes": {
                "columns": [
                    {
                        "name": "id_clientes",
                        "type": "int",
                        "nullable": False,
                        "key": "PRI"
                    },
                    ...
                ]
            },
            ...
        }
        """

        # =========================
        # 1️⃣ Obtener modelos activos
        # =========================
        models = MySQLMetadataService._get_active_models(company)

        if not models:
            return {}

        # =========================
        # 2️⃣ Infraestructura MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        schema_metadata = {}

        # =========================
        # 3️⃣ Consultar INFORMATION_SCHEMA
        # =========================
        for model in models:

            table_name = model["tabla"]

            sql = """
                SELECT
                    COLUMN_NAME,
                    COLUMN_TYPE,
                    IS_NULLABLE,
                    COLUMN_KEY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = %s
                ORDER BY ORDINAL_POSITION
            """

            columns = dml.fetch_all(sql, (table_name,))

            formatted_columns = []

            for col in columns:
                formatted_columns.append(
                    {
                        "name": col["COLUMN_NAME"],
                        "type": col["COLUMN_TYPE"],
                        "nullable": col["IS_NULLABLE"] == "YES",
                        "key": col["COLUMN_KEY"],  # PRI / MUL / ''
                    }
                )

            schema_metadata[table_name] = {
                "columns": formatted_columns
            }

        try:
            connection.close()
        except Exception:
            pass

        return schema_metadata

    # ==================================================
    # Internos
    # ==================================================

    @staticmethod
    def _get_active_models(company) -> list[dict]:
        """
        Obtiene todos los modelos activos de todos los módulos.
        """

        # Obtener módulos activos
        # (No filtramos por módulo aquí porque
        # el reporte puede cruzar tablas)
        modules = []

        from core.db.mongo.services.modules.module_query_service import (
            ModuleQueryService,
        )

        modules = ModuleQueryService.get_active_modules(company)

        models = []

        for module in modules:
            module_id = module["_id"]
            module_models = ModelQueryService.get_models_for_module(
                company=company,
                module_id=module_id,
            )
            models.extend(module_models)

        return models