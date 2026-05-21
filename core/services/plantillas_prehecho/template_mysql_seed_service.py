# core/services/plantillas_prehecho/template_mysql_seed_service.py

from core.db.mysql.services.connection_service import (MySQLCompanyConnectionService)
from core.db.mysql.executor import (MySQLExecutor)
from core.db.mysql.services.dml_service import (MySQLDMLService)
from core.db.mysql.sql.sql_generator import (SQLGenerator)

from core.services.plantillas_prehecho.template_mysql_table_query_service import (TemplateMySQLTableQueryService)


class TemplateMySQLSeedService:
    """
    Servicio encargado de insertar
    data inicial MySQL definida
    en ejecuciones de plantilla.

    Reglas:
    - Si tabla NO existe → skip
    - Si tabla tiene registros → skip
    - Si tabla está vacía → insertar
    """

    # =========================
    # Ejecutar seed MySQL
    # =========================
    @staticmethod
    def execute_seed(*, company, ejecuciones):
        """
        Ejecuta inserts iniciales MySQL
        para todas las ejecuciones activas.
        """

        # =========================
        # Obtener tablas existentes
        # =========================
        existing_tables = TemplateMySQLTableQueryService.get_existing_tables(
            company=company,
        )

        existing_tables_set = set(existing_tables)

        # =========================
        # Conexión MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        inserted_tables = []
        skipped_tables = []

        try:
            with dml.transaction():
                for ejecucion in ejecuciones:
                    data_inicial_mysql = ejecucion.data_inicial_mysql or []

                    if not data_inicial_mysql:
                        continue

                    # =========================
                    # Recorrer tablas seed
                    # =========================
                    for item in data_inicial_mysql:
                        table_name = item.get("tabla")
                        registros = item.get("registros", [])

                        if not table_name:
                            continue
                        if not registros:
                            continue

                        # =========================
                        # Tabla no existe
                        # =========================
                        if table_name not in existing_tables_set:
                            skipped_tables.append(
                                {
                                    "table": table_name,
                                    "reason": "table_not_exists",
                                }
                            )
                            continue

                        # =========================
                        # Validar registros existentes
                        # =========================
                        total_records = TemplateMySQLTableQueryService.count_records_for_table(
                            company=company,
                            table_name=table_name,
                        )

                        # =========================
                        # Tabla ya contiene registros
                        # =========================
                        if total_records > 0:
                            skipped_tables.append(
                                {
                                    "table": table_name,
                                    "reason": "table_has_records",
                                    "record_count": total_records,
                                }
                            )
                            continue

                        # =========================
                        # Insertar registros
                        # =========================
                        inserted_count = 0
                        for registro in registros:
                            sql, params = SQLGenerator.insert(
                                table_name=f"`{table_name}`",
                                data=registro,
                            )
                            dml.insert(sql,params)
                            inserted_count += 1

                        inserted_tables.append(
                            {
                                "table": table_name,
                                "inserted_count": inserted_count,
                            }
                        )

        finally:
            try:
                connection.close()
            except Exception:
                pass

        # =========================
        # Resultado final
        # =========================
        return {
            "success": True,
            "inserted_tables": inserted_tables,
            "skipped_tables": skipped_tables,
        }