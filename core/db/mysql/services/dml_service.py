# core/db/mysql/services/dml_service.py
# ====================================
# Servicio DML MySQL (INSERT / UPDATE / DELETE / SELECT)
# ====================================

from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.sql.sql_validator import SQLValidator
from core.db.mysql.exceptions import (
    MySQLServiceError,
    MySQLExecutionError,
    MySQLIntegrityError,
)


class MySQLDMLService:
    """
    Servicio encargado de ejecutar operaciones DML
    de forma segura y controlada.

    Responsabilidades:
    - Validar SQL DML
    - Ejecutar SQL usando MySQLExecutor
    - Manejar transacciones
    - Normalizar errores
    """

    def __init__(self, executor: MySQLExecutor):
        if not executor:
            raise MySQLServiceError("Executor MySQL no proporcionado")

        self.executor = executor

    # =========================
    # INSERT
    # =========================

    def insert(self, sql: str, params: tuple | dict) -> int:
        """
        Ejecuta un INSERT.

        Retorna:
        - Número de filas insertadas
        """
        return self._execute_dml(
            sql=sql,
            params=params,
            fetch=None,
        )

    # =========================
    # UPDATE
    # =========================

    def update(self, sql: str, params: tuple | dict) -> int:
        """
        Ejecuta un UPDATE.

        Retorna:
        - Número de filas afectadas
        """
        return self._execute_dml(
            sql=sql,
            params=params,
            fetch=None,
        )

    # =========================
    # DELETE
    # =========================

    def delete(self, sql: str, params: tuple | dict) -> int:
        """
        Ejecuta un DELETE.

        Retorna:
        - Número de filas eliminadas
        """
        return self._execute_dml(
            sql=sql,
            params=params,
            fetch=None,
        )

    # =========================
    # SELECT
    # =========================

    def fetch_one(self, sql: str, params: tuple | dict | None = None) -> dict | None:
        """
        Ejecuta SELECT que retorna una sola fila.
        """
        return self._execute_dml(
            sql=sql,
            params=params,
            fetch="one",
        )

    def fetch_all(self, sql: str, params: tuple | dict | None = None) -> list[dict]:
        """
        Ejecuta SELECT que retorna múltiples filas.
        """
        return self._execute_dml(
            sql=sql,
            params=params,
            fetch="all",
        )
    
        # =========================
    # SELECT estructurado
    # =========================

    def fetch_all_structured(self,sql: str,params: tuple | dict | None = None,) -> tuple[list[str], list[list]]:
        """
        Ejecuta un SELECT y retorna:

        (
            [column_names],
            [
                [row_values],
                ...
            ]
        )

        El orden de los valores respeta el orden
        de las columnas retornadas por el cursor.
        """

        try:
            # 1️⃣ Validar SQL
            SQLValidator.validate(sql)

            # 2️⃣ Ejecutar directamente con cursor
            with self.executor.connection.cursor() as cursor:
                cursor.execute(sql, params)

                # Columnas desde description
                column_names = [col[0] for col in cursor.description]

                # Filas como listas de valores
                rows = [
                    [row[col] for col in column_names]
                    for row in cursor.fetchall()
                ]


                return column_names, rows

        except MySQLIntegrityError:
            raise

        except MySQLServiceError:
            raise

        except Exception as e:
            raise MySQLExecutionError(
                "Error al ejecutar SELECT estructurado",
                original_exception=e,
            )


    # =========================
    # Transacciones explícitas
    # =========================

    def transaction(self):
        """
        Context manager de transacción DML.

        Uso:
            with dml.transaction():
                dml.insert(...)
                dml.update(...)
        """
        return self.executor.transaction()

    # =========================
    # Ejecutor interno
    # =========================

    def _execute_dml(self, *, sql: str, params, fetch):
        """
        Flujo único para ejecutar DML.
        """

        try:
            # 1️⃣ Validar SQL
            SQLValidator.validate(sql)

            # 2️⃣ Ejecutar
            if fetch == "one":
                return self.executor.fetch_one(sql, params)

            if fetch == "all":
                return self.executor.fetch_all(sql, params)

            return self.executor.execute(sql, params)

        except MySQLIntegrityError:
            # Violaciones de integridad → propagar
            raise

        except MySQLServiceError:
            # Errores propios → propagar
            raise

        except Exception as e:
            # Normalizar cualquier otro error
            raise MySQLExecutionError(
                "Error al ejecutar operación DML",
                original_exception=e,
            )
