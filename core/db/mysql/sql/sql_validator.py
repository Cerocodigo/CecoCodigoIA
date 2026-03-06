# core/db/mysql/sql/sql_validator.py
# =================================
# Validador de SQL seguro
# =================================
# - Valida estructura
# - Aplica listas blancas
# - Bloquea SQL peligroso
# =================================

import re

from core.db.mysql.exceptions import MySQLExecutionError


class SQLValidator:
    """
    Validador de sentencias SQL generadas por el sistema.

    IMPORTANTE:
    - No valida SQL arbitrario
    - Solo valida SQL generado por SQLGenerator
    """

    # =========================
    # Reglas generales
    # =========================

    FORBIDDEN_KEYWORDS = [
        "drop database",
        "truncate",
        "union",
        ";",
        "--",
        "/*",
        "*/",
    ]

    # =========================
    # DDL permitido
    # =========================

    ALLOWED_DDL_PREFIXES = [
        "create table",
        "alter table",
        "drop table",
    ]

    # =========================
    # DML permitido
    # =========================

    ALLOWED_DML_PREFIXES = [
        "insert into",
        "update",
        "delete from",
        "select",
    ]

    # =========================
    # API pública
    # =========================

    @classmethod
    def validate(cls, sql: str):
        """
        Punto de entrada único.
        """

        if not sql or not isinstance(sql, str):
            raise MySQLExecutionError("SQL vacío o inválido")

        sql_clean = cls._normalize(sql)

        cls._check_forbidden(sql_clean)
        cls._check_allowed(sql_clean)
        cls._check_structure(sql_clean)

    # =========================
    # Normalización
    # =========================

    @staticmethod
    def _normalize(sql: str) -> str:
        """
        Normaliza SQL para validación:
        - minúsculas
        - espacios simples
        """

        return re.sub(r"\s+", " ", sql.strip().lower())

    # =========================
    # Reglas
    # =========================

    @classmethod
    def _check_forbidden(cls, sql: str):
        for keyword in cls.FORBIDDEN_KEYWORDS:
            if keyword in sql:
                raise MySQLExecutionError(
                    f"SQL contiene instrucción prohibida: '{keyword}'"
                )

    @classmethod
    def _check_allowed(cls, sql: str):
        """
        Verifica que el SQL empiece con una instrucción permitida.
        """

        allowed_prefixes = cls.ALLOWED_DDL_PREFIXES + cls.ALLOWED_DML_PREFIXES

        if not any(sql.startswith(prefix) for prefix in allowed_prefixes):
            raise MySQLExecutionError(
                "Tipo de operación SQL no permitida"
            )

    @classmethod
    def _check_structure(cls, sql: str):
        """
        Reglas estructurales mínimas.
        """

        # UPDATE sin WHERE = NO
        if sql.startswith("update") and " where " not in sql:
            raise MySQLExecutionError(
                "UPDATE sin WHERE no está permitido"
            )

        # DELETE sin WHERE = NO
        if sql.startswith("delete") and " where " not in sql:
            raise MySQLExecutionError(
                "DELETE sin WHERE no está permitido"
            )

