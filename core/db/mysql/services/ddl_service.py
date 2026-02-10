# core/db/mysql/services/ddl_service.py
# ====================================
# Servicio DDL MySQL (CREATE / ALTER / DROP)
# ====================================

from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.sql.sql_validator import SQLValidator
from core.db.mysql.exceptions import (
    MySQLServiceError,
    MySQLExecutionError,
)


class MySQLDDLService:
    """
    Servicio encargado de ejecutar operaciones DDL
    de forma segura y controlada.

    Responsabilidades:
    - Validar SQL DDL
    - Ejecutar SQL usando MySQLExecutor
    - Normalizar errores
    """

    def __init__(self, executor: MySQLExecutor):
        if not executor:
            raise MySQLServiceError("Executor MySQL no proporcionado")

        self.executor = executor

    # =========================
    # API pública
    # =========================

    def create_table(self, sql: str) -> None:
        """
        Ejecuta CREATE TABLE.
        """
        self._execute_ddl(sql)

    def alter_table(self, sql: str) -> None:
        """
        Ejecuta ALTER TABLE.
        """
        self._execute_ddl(sql)

    def drop_table(self, sql: str) -> None:
        """
        Ejecuta DROP TABLE.

        NOTA:
        - Permitido solo porque el SQLValidator lo controla
        - Fácil de bloquear por entorno en el futuro
        """
        self._execute_ddl(sql)

    # =========================
    # Ejecutor interno
    # =========================

    def _execute_ddl(self, sql: str) -> None:
        """
        Flujo único y obligatorio para ejecutar DDL.
        """

        try:
            # 1️⃣ Validar SQL
            SQLValidator.validate(sql)

            # 2️⃣ Ejecutar
            self.executor.execute(sql)

        except MySQLServiceError:
            # Errores propios: re-lanzar
            raise

        except Exception as e:
            # Cualquier otro error → normalizar
            raise MySQLExecutionError(
                "Error al ejecutar operación DDL",
                original_exception=e,
            )
