# core/db/mysql/executor.py
# ===========================================
# Ejecutor SQL seguro para MySQL / MariaDB
# ===========================================

from contextlib import contextmanager

from core.db.mysql.exceptions import (
    MySQLServiceError,
    MySQLExecutionError,
    MySQLIntegrityError,
)
from pymysql.connections import Connection


class MySQLExecutor:
    """
    Ejecuta sentencias SQL de forma segura y controlada.

    - NO crea conexiones
    - NO expone cursores
    - NO contiene lógica de negocio
    - Soporta transacciones
    """

    def __init__(self, connection: Connection):
        if not connection:
            raise MySQLServiceError("Conexión MySQL no proporcionada")

        self.connection = connection

    # =========================
    # Métodos públicos
    # =========================

    def execute(self, sql: str, params: tuple | dict | None = None) -> int:
        """
        Ejecuta INSERT / UPDATE / DELETE / DDL.

        Retorna:
        - Número de filas afectadas
        """
        return self._execute_internal(
            sql=sql,
            params=params,
            fetch=None
        )

    def fetch_one(self, sql: str, params: tuple | dict | None = None) -> dict | None:
        """
        Ejecuta SELECT que retorna una sola fila.

        Retorna:
        - dict si hay resultado
        - None si no hay filas
        """
        return self._execute_internal(
            sql=sql,
            params=params,
            fetch="one"
        )

    def fetch_all(self, sql: str, params: tuple | dict | None = None) -> list[dict]:
        """
        Ejecuta SELECT que retorna múltiples filas.

        Retorna:
        - Lista de dicts (vacía si no hay resultados)
        """
        return self._execute_internal(
            sql=sql,
            params=params,
            fetch="all"
        )

    def execute_many(self, sql: str, params_list: list[tuple | dict]) -> int:
        """
        Ejecuta una sentencia SQL en batch.

        Retorna:
        - Total de filas afectadas
        """
        if not params_list:
            return 0

        try:
            with self.connection.cursor() as cursor:
                cursor.executemany(sql, params_list)
                self.connection.commit()
                return cursor.rowcount

        except Exception as e:
            self.connection.rollback()
            self._raise_mysql_exception(e)

    # =========================
    # Transacciones
    # =========================

    @contextmanager
    def transaction(self):
        """
        Context manager para ejecutar múltiples operaciones
        dentro de una transacción.

        Uso:
            with executor.transaction():
                executor.execute(...)
                executor.execute(...)
        """
        try:
            yield
            self.connection.commit()
        except Exception as e:
            self.connection.rollback()
            self._raise_mysql_exception(e)

    # =========================
    # Ejecutor interno
    # =========================

    def _execute_internal(self, *, sql, params, fetch):
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params or ())

                if fetch == "one":
                    row = cursor.fetchone()
                    return row

                if fetch == "all":
                    return cursor.fetchall()

                # execute normal
                self.connection.commit()
                return cursor.rowcount

        except Exception as e:
            self.connection.rollback()
            self._raise_mysql_exception(e)

    # =========================
    # Normalización de errores
    # =========================

    def _raise_mysql_exception(self, exception: Exception):
        """
        Convierte excepciones del driver MySQL
        en excepciones propias del sistema.
        """

        error_name = exception.__class__.__name__.lower()

        if "integrity" in error_name or "duplicate" in str(exception).lower():
            raise MySQLIntegrityError(str(exception))

        raise MySQLExecutionError(str(exception))
