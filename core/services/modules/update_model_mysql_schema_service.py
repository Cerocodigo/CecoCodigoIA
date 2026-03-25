# core/services/modules/update_model_mysql_schema_service.py
# ==================================================
# Servicio de sincronización MongoDB → MySQL
# ==================================================

from core.db.mongo.services.models.model_query_service import (
    ModelQueryService,
)

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.ddl_service import MySQLDDLService
from core.db.mysql.sql.sql_generator import SQLGenerator

from core.services.modules.mongo_to_mysql_field_mapper import (
    mongo_field_to_sql,
)

from core.services.modules.model_validator_service import (
    ModelValidatorService,
)

from core.services.modules.column_comparator_service import (
    ColumnComparatorService,
)


class UpdateModelMySQLSchemaService:
    """
    Servicio transversal encargado de sincronizar
    la estructura MySQL a partir de un modelo MongoDB.
    """

    # =========================
    # API pública
    # =========================

    @staticmethod
    def update_schema_for_model(*, company, model_id: str):
        """
        Punto de entrada único.

        - Obtiene el modelo desde MongoDB
        - Valida el modelo
        - Sincroniza la tabla MySQL asociada
        """

        # =========================
        # 1️⃣ Obtener modelo Mongo
        # =========================
        model = ModelQueryService.get_model_by_id(
            company=company,
            model_id=model_id,
            is_raw=True,
        )

        if not model:
            raise ValueError("Modelo MongoDB no encontrado")

        # =========================
        # 2️⃣ VALIDAR MODELO
        # =========================
        validation = ModelValidatorService.validate(model)

        if not validation["is_valid"]:
            error_messages = "\n".join(
                [f"{e['path']}: {e['message']}" for e in validation["errors"]]
            )
            raise ValueError(
                f"Modelo inválido. Corrige los siguientes errores:\n{error_messages}"
            )

        table_name = model["tabla"]
        campos = model.get("campos", [])

        # =========================
        # 3️⃣ Infraestructura MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        ddl = MySQLDDLService(executor)

        # =========================
        # 4️⃣ Verificar si la tabla existe
        # =========================
        sql_exists = """
            SELECT COUNT(*) AS total
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = %s
        """

        result = executor.fetch_one(sql_exists, (table_name,))
        table_exists = result["total"] == 1

        # =========================
        # 5️⃣ Convertir campos Mongo → SQL
        # =========================
        mongo_columns = {
            campo["nombre"]: mongo_field_to_sql(campo)
            for campo in campos
        }

        # =========================
        # 6️⃣ Crear tabla si no existe
        # =========================
        if not table_exists:
            sql, _ = SQLGenerator.create_table(
                table_name=table_name,
                columns=list(mongo_columns.values()),
            )
            ddl.create_table(sql)
            return

        # =========================
        # 7️⃣ Obtener columnas MySQL existentes
        # =========================
        sql_columns = """
            SELECT
                column_name,
                column_type,
                is_nullable,
                extra
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
        """

        rows = executor.fetch_all(sql_columns, (table_name,))

        mysql_columns = {
            row["column_name"]: row
            for row in rows
        }

        # =========================
        # 8️⃣ Comparar y sincronizar
        # =========================

        # 8.1 ➕ Columnas nuevas
        for name, definition in mongo_columns.items():
            if name not in mysql_columns:
                sql, _ = SQLGenerator.add_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

        # 8.2 🔄 Columnas modificadas (solo si hay cambios reales)
        for name, definition in mongo_columns.items():
            if name in mysql_columns:

                # ⚠️ No modificar PRIMARY KEY
                if "PRIMARY KEY" in definition:
                    continue

                mysql_column = mysql_columns[name]

                if not ColumnComparatorService.has_changes(mysql_column, definition):
                    continue  # 👈 NO hacer ALTER innecesario

                sql, _ = SQLGenerator.modify_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

        # 8.3 ➖ Columnas sobrantes
        for name in mysql_columns.keys():
            if name not in mongo_columns:
                sql, _ = SQLGenerator.drop_column(
                    table_name=table_name,
                    column_name=name,
                )
                ddl.alter_table(sql)