# core/services/modules/delete_module_record_service.py
# =====================================================
# Servicio para eliminar registros de módulos (cabecera + detalle)
# =====================================================

from core.db.mongo.services.modules.module_query_service import ModuleQueryService
from core.db.mongo.services.models.model_query_service import ModelQueryService

from core.db.mysql.services.connection_service import MySQLCompanyConnectionService
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService


class DeleteModuleRecordService:

    @staticmethod
    def execute(company, module_id: str, record_id: int):
        """
        Elimina un registro completo:
        - Detalles primero
        - Cabecera después

        Retorna:
            (success: bool, error: str | None)
        """

        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            # =========================
            # Obtener metadata
            # =========================
            module = ModuleQueryService.get_module_by_id(
                company=company,
                module_id=module_id,
            )

            if not module:
                return False, "Módulo no encontrado"

            modelo_cab = ModelQueryService.get_models_for_module_rol(
                company=company,
                module_id=module_id,
                module_rol="cabecera"
            )[0]

            modelos_det = ModelQueryService.get_models_for_module_rol(
                company=company,
                module_id=module_id,
                module_rol="detalle"
            )

            # =========================
            # DELETE transaccional
            # =========================
            with dml.transaction():

                # 🔥 eliminar detalles primero
                for det in modelos_det:
                    sql = f"DELETE FROM {det['tabla']} WHERE {det['fk']} = %s"
                    dml.delete(sql, (record_id,))

                # 🔥 eliminar cabecera
                sql = f"DELETE FROM {modelo_cab['tabla']} WHERE {modelo_cab['pk']} = %s"
                dml.delete(sql, (record_id,))

            return True, None

        except Exception as e:
            return False, str(e)

        finally:
            try:
                connection.close()
            except Exception:
                pass