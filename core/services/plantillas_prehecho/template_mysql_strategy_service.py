# core/services/plantillas_prehecho/template_mysql_strategy_service.py

from core.db.sqlite.models.modelo_prehecho_jsons import (ModeloPrehechoJsons)

from core.services.modules.ensure_model_schema_service import (EnsureModelSchemaService)

from core.services.plantillas_prehecho.template_mysql_table_query_service import (TemplateMySQLTableQueryService)

from core.db.mysql.services.connection_service import (MySQLCompanyConnectionService)

from core.db.mysql.executor import (MySQLExecutor)

from core.db.mysql.services.ddl_service import (MySQLDDLService)

from core.db.mysql.sql.sql_generator import (SQLGenerator)

# =========================
# Helper de normalización JSON
# =========================
def normalize_model(model):
    if not isinstance(model, dict):
        return model

    if "creado_en" in model and isinstance(model["creado_en"], dict):
        model["creado_en"] = model["creado_en"].get("$date")

    return model

class TemplateMySQLStrategyService:
    """
    Servicio encargado de ejecutar
    estrategias de sincronización MySQL
    durante aplicación de plantillas.

    Estrategias soportadas:
    - clean
    - keep
    """

    # =========================
    # Ejecutar estrategia
    # =========================
    @staticmethod
    def execute_strategy(*, company, plantilla, strategy):
        """
        Punto central de ejecución
        de estrategia MySQL.
        """
        print("Estrategia seleccionada:", strategy)
        if strategy == "clean":
            return (
                TemplateMySQLStrategyService.execute_clean_strategy(
                    company=company,
                    plantilla=plantilla,
                )
            )

        if strategy == "keep":
            return (
                TemplateMySQLStrategyService.execute_keep_strategy(
                    company=company,
                    plantilla=plantilla,
                )
            )

        raise ValueError(
            f"Estrategia inválida: {strategy}"
        )

    # =========================
    # Estrategia CLEAN
    # =========================
    @staticmethod
    def execute_clean_strategy(*, company, plantilla):
        """
        Estrategia limpia:

        - Elimina TODAS las tablas MySQL
        - Re-crea estructura usando modelos
          de la plantilla
        """

        # =========================
        # Obtener modelos plantilla
        # =========================
        models = TemplateMySQLStrategyService.get_template_models(
            plantilla=plantilla,
        )


        # =========================
        # Obtener tablas actuales
        # =========================
        existing_tables = TemplateMySQLTableQueryService.get_existing_tables(
            company=company,
        )


        # =========================
        # Eliminar tablas
        # =========================
        dropped_tables = TemplateMySQLStrategyService.drop_tables(
            company=company,
            table_names=existing_tables,
        )

        # =========================
        # Re-crear esquema
        # =========================
        ensure_result = EnsureModelSchemaService.ensure_model_schema(
            company=company,
            models=models,
        )

        # =========================
        # Resultado
        # =========================
        return {
            "success": ensure_result["success"],
            "strategy": "clean",
            "dropped_tables": dropped_tables,
            "ensure_result": ensure_result,
        }

    # =========================
    # Estrategia KEEP
    # =========================
    @staticmethod
    def execute_keep_strategy(*, company, plantilla):
        """
        Estrategia conservadora:

        - Mantiene tablas compatibles
        - Elimina tablas obsoletas
        - Crea tablas faltantes
        - Conserva registros existentes
        """

        # =========================
        # Obtener modelos plantilla
        # =========================
        models = TemplateMySQLStrategyService.get_template_models(
            plantilla=plantilla,
        )


        # =========================
        # Obtener tablas actuales
        # =========================
        existing_tables = TemplateMySQLTableQueryService.get_existing_tables(
            company=company,
        )


        # =========================
        # Obtener tablas plantilla
        # =========================
        template_tables = []

        for model in models:
            table_name = model.get("tabla")
            if not table_name:
                continue

            template_tables.append(table_name)

        template_tables_set = set(template_tables)

        print("--------------------------------")
        print("Tablas existentes:", existing_tables)
        print("Tablas en plantilla:", template_tables)
        print("--------------------------------")

        # =========================
        # Detectar tablas obsoletas
        # =========================
        obsolete_tables = []

        for table_name in existing_tables:
            if table_name not in template_tables_set:
                obsolete_tables.append(table_name)

        # =========================
        # Eliminar tablas obsoletas
        # =========================
        dropped_tables = TemplateMySQLStrategyService.drop_tables(
            company=company,
            table_names=obsolete_tables,
        )


        # =========================
        # Garantizar tablas faltantes
        # =========================
        ensure_result = EnsureModelSchemaService.ensure_model_schema(
            company=company,
            models=models,
        )


        # =========================
        # Resultado
        # =========================
        return {
            "success": ensure_result["success"],
            "strategy": "keep",
            "obsolete_tables": obsolete_tables,
            "dropped_tables": dropped_tables,
            "ensure_result": ensure_result,
        }

    # =========================
    # Eliminar tablas
    # =========================
    @staticmethod
    def drop_tables(*, company, table_names):
        """
        Elimina múltiples tablas MySQL
        de forma segura usando infraestructura oficial.
        """

        if not table_names:
            return []

        # =========================
        # Conexión MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        ddl_service = MySQLDDLService(executor)

        dropped_tables = []

        try:
            # =========================
            # Desactivar FK checks
            # =========================
            executor.execute("SET FOREIGN_KEY_CHECKS = 0")

            # =========================
            # Eliminar tablas
            # =========================
            for table_name in table_names:
                sql, _ = SQLGenerator.drop_table(table_name=f"`{table_name}`")

                ddl_service.drop_table(sql)

                dropped_tables.append(table_name)

            # =========================
            # Reactivar FK checks
            # =========================
            executor.execute("SET FOREIGN_KEY_CHECKS = 1")

        finally:
            try:
                connection.close()
            except Exception:
                pass

        return dropped_tables

    # =========================
    # Obtener modelos plantilla
    # =========================
    @staticmethod
    def get_template_models(*, plantilla,):
        """
        Retorna modelos Mongo
        definidos en plantilla.
        """

        template_models_json = ModeloPrehechoJsons.objects.filter(
            modelo=plantilla,
            activo=True,
            tipo="modelos",
        ).order_by("id")

        models = []

        for item in template_models_json:
            json_data = item.json
            if not json_data:
                continue
            # CASO 1: si ya es lista (tu caso real)
            if isinstance(json_data, list):
                models.extend([normalize_model(item) for item in json_data])
                continue

            # CASO 2: si fuera dict individual
            if isinstance(json_data, dict):
                models.append(normalize_model(json_data))
                continue

        return models