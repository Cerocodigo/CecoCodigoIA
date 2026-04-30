# core/services/modules/ensure_model_schema_service.py

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor

from core.services.modules.model_sync_orchestrator_service import (
    ModelSyncOrchestratorService,
)

from core.services.modules.update_model_mysql_schema_service import (
    UpdateModelMySQLSchemaService,
)


class EnsureModelSchemaService:
    """
    Servicio de validación y sincronización de esquema MySQL
    para todos los modelos de un módulo.

    Flujo por cada modelo:
    1. Verificar si la tabla MySQL existe
    2. Si no existe → Validar modelo
    3. Si es válido → Sincronizar esquema MySQL

    Garantiza:
    - No intentar sincronizar modelos inválidos
    - No detener todo el proceso si una tabla ya existe
    - Consolidar el resultado final de todos los modelos
    """

    @staticmethod
    def ensure_model_schema(company, models):
        """
        Retorna:

        {
            "success": bool,
            "results": [
                {
                    "model_id": str,
                    "table": str,
                    "success": bool,
                    "action": "exists" | "created" | "validation_error" | "sync_error",
                    "errors": list,
                    "sync_result": dict | None
                }
            ]
        }
        """

        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)

        overall_success = True
        results = []

        # =========================
        # Recorrer todos los modelos del módulo
        # =========================
        for model in models:
            table_name = model["tabla"]
            model_id = model.get("_id", "")

            # =========================
            # 1. Verificar si la tabla MySQL existe
            # =========================
            sql_exists = """
                SELECT COUNT(*) AS total
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
                  AND table_name = %s
            """

            result = executor.fetch_one(sql_exists, (table_name,))
            table_exists = result["total"] == 1

            # Si ya existe → continuar con el siguiente modelo
            if table_exists:
                results.append({
                    "model_id": model_id,
                    "table": table_name,
                    "success": True,
                    "action": "exists",
                    "errors": [],
                    "sync_result": None,
                })
                continue

            # =========================
            # 2. Validar modelo
            # =========================
            validation_result = ModelSyncOrchestratorService.process_model(model)

            if not validation_result["success"]:
                overall_success = False

                results.append({
                    "model_id": model_id,
                    "table": table_name,
                    "success": False,
                    "action": "validation_error",
                    "errors": validation_result.get("errors", []),
                    "sync_result": None,
                })

                continue

            # =========================
            # 3. Sincronizar esquema MySQL
            # =========================
            try:
                sync_result = UpdateModelMySQLSchemaService.sync_schema_for_model(
                    model=validation_result["final_model"],
                    company=company,
                )

                sync_success = sync_result.get("success", True)

                if not sync_success:
                    overall_success = False

                results.append({
                    "model_id": model_id,
                    "table": table_name,
                    "success": sync_success,
                    "action": "created" if sync_success else "sync_error",
                    "errors": sync_result.get("errors", []),
                    "sync_result": sync_result,
                })

            except Exception as e:
                overall_success = False

                results.append({
                    "model_id": model_id,
                    "table": table_name,
                    "success": False,
                    "action": "sync_error",
                    "errors": [str(e)],
                    "sync_result": None,
                })

        return {
            "success": overall_success,
            "results": results,
        }