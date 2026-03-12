# core/db/mysql/exceptions.py
# ==========================
# Excepciones controladas para MySQL
# ==========================


class MySQLServiceError(Exception):
    """
    Error base para cualquier fallo relacionado con MySQL.
    """

    def __init__(self, message: str, *, original_exception: Exception | None = None):
        super().__init__(message)
        self.original_exception = original_exception


class MySQLConfigurationError(MySQLServiceError):
    """
    Error de configuración (credenciales, base inexistente, etc).
    """
    pass


class MySQLConnectionError(MySQLServiceError):
    """
    Error al intentar establecer conexión con MySQL.
    """
    pass


class MySQLExecutionError(MySQLServiceError):
    """
    Error al ejecutar una operación SQL.
    """
    pass

class MySQLIntegrityError(MySQLServiceError):
    """
    Error de integridad de datos (UNIQUE, FK, NOT NULL, etc).
    """
    pass
