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
    '''
    Servicio de validación y sincronización de esquema MySQL para un modelo dado.
    Flujo:
    1. Verificar si la tabla MySQL existe
    2. Si no existe → Validar modelo
    3. Si es válido → Sincronizar esquema MySQL
    Garantiza:
    - No intentar sincronizar modelos inválidos
    - Retornar resultados claros para la capa de vista
    '''

    @staticmethod
    def ensure_model_schema(company, model):
        '''
        Retorna:
        {
            "success": bool,
            "error": str (si success=False),
            "sync_result": dict (si success=True)
        }
        '''

        table_name = model["tabla"]

        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)

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

        if table_exists:
            return {
                "success": True,
                "action": "exists"
            }

        # =========================
        # 2. Validar modelo
        # =========================
        result = ModelSyncOrchestratorService.process_model(model)

        if not result["success"]:
            return {
                "success": False,
                "stage": "validation",
                "errors": result.get("errors", [])
            }
        
        # =========================
        # 3. Sincronizar esquema MySQL
        # =========================
        sync_result = UpdateModelMySQLSchemaService.sync_schema_for_model(
            model=result["final_model"],
            company=company,
        )

        return {
            "success": True,
            "action": "created",
            "sync_result": sync_result
        }