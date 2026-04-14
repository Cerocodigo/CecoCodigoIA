# core/services/modules/update_model_mysql_schema_service.py
# ==================================================
# Servicio de sincronización MongoDB → MySQL
# ==================================================

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.ddl_service import MySQLDDLService
from core.db.mysql.sql.sql_generator import SQLGenerator

from core.services.modules.mongo_to_mysql_field_mapper import (
    mongo_field_to_sql,
)

from core.services.modules.column_comparator_service import (
    ColumnComparatorService,
)



class UpdateModelMySQLSchemaService:
    """
    Servicio encargado EXCLUSIVAMENTE de sincronizar
    la estructura MySQL a partir de un modelo YA validado.

    NO:
    - valida
    - corrige
    - consulta Mongo
    """

    # =========================
    # ENTRYPOINT
    # =========================

    @staticmethod
    def sync_schema_for_model(model: dict, company):
        """
        Ejecuta sincronización directa.

        PRECONDICIÓN:
        - El modelo ya fue validado y corregido

        Retorna:
        {
            "table": str,
            "created": bool,
            "columns_added": [],
            "columns_modified": [],
            "columns_deleted": []
        }
        """           


        table_name = model["tabla"]
        campos = model.get("campos", [])

        # =========================
        # Infraestructura MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        ddl = MySQLDDLService(executor)

        # =========================
        # Verificar existencia tabla
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
        # Convertir campos Mongo → SQL
        # =========================
        mongo_columns = {
            campo["nombre"]: mongo_field_to_sql(campo)
            for campo in campos
        }

        # =========================
        # RESULTADO TRACKING
        # =========================
        result_summary = {
            "table": table_name,
            "created": False,
          "columns_added": [],
            "columns_modified": [],
            "columns_deleted": [],
            "synchronization_executed": False,
        }

        # =========================
        # Crear tabla
        # =========================
        if not table_exists:
            sql, _ = SQLGenerator.create_table(
                table_name=table_name,
                columns=list(mongo_columns.values()),
            )
            ddl.create_table(sql)

            result_summary["created"] = True
            result_summary["columns_added"] = list(mongo_columns.keys())
            result_summary["synchronization_executed"] = True

            return result_summary

        # =========================
        # Obtener columnas actuales
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
        # ➕ COLUMNAS NUEVAS
        # =========================
        for name, definition in mongo_columns.items():
            if name not in mysql_columns:
                sql, _ = SQLGenerator.add_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

                result_summary["columns_added"].append(name)
                result_summary["synchronization_executed"] = True
        # =========================
        # 🔄 COLUMNAS MODIFICADAS
        # =========================
        for name, definition in mongo_columns.items():
            if name in mysql_columns:

                # ⚠️ NO tocar PK
                if "PRIMARY KEY" in definition:
                    continue

                mysql_column = mysql_columns[name]

                if not ColumnComparatorService.has_changes(mysql_column, definition):
                    continue

                sql, _ = SQLGenerator.modify_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

                result_summary["columns_modified"].append(name)
                result_summary["synchronization_executed"] = True

        # =========================
        # ➖ COLUMNAS ELIMINADAS
        # =========================
        for name in mysql_columns.keys():
            if name not in mongo_columns:
                sql, _ = SQLGenerator.drop_column(
                    table_name=table_name,
                    column_name=name,
                )
                ddl.alter_table(sql)

                result_summary["columns_deleted"].append(name)
                result_summary["synchronization_executed"] = True


        if len(result_summary["columns_deleted"]) == 0 and len(result_summary["columns_modified"]) == 0 and len(result_summary["columns_added"]) == 0:
            result_summary["synchronization_executed"] = True

        return result_summary
