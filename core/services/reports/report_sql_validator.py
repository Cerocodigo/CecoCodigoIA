# core/services/reports/report_sql_validator.py
# ==================================================
# Validador técnico de seguridad SQL para reportes
# ==================================================

import re


class ReportSQLValidator:
    """
    Validador técnico de SQL.

    Responsabilidades:
    - Permitir solo SELECT / WITH
    - Bloquear múltiples statements
    - Bloquear comentarios
    - Bloquear palabras prohibidas
    - Validar parámetros permitidos por nivel
    - Bloquear dependencia entre niveles vía parámetros dinámicos

    NO valida estructura JSON del reporte.
    NO ejecuta SQL.
    """

    FORBIDDEN_KEYWORDS = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
        "RENAME",
        "GRANT",
        "REVOKE",
        "CALL",
        "EXEC",
        "EXECUTE",
    ]

    PARAM_PATTERN = r":([a-zA-Z_][a-zA-Z0-9_]*)"

    # ==================================================
    # VALIDACIÓN BÁSICA DE SEGURIDAD
    # ==================================================
    @classmethod
    def validate_sql(cls, sql: str) -> dict:
        """
        Valida seguridad básica del SQL.
        """

        errors = []

        if not sql or not sql.strip():
            errors.append("El SQL no puede estar vacío.")
            return {"is_valid": False, "errors": errors}

        sql_clean = sql.strip()
        sql_upper = sql_clean.upper()

        # 1️⃣ Debe comenzar con SELECT o WITH
        if not (
            sql_upper.startswith("SELECT")
            or sql_upper.startswith("WITH")
        ):
            errors.append(
                "El SQL debe comenzar con SELECT o WITH."
            )

        # 2️⃣ No múltiples statements (;)
        semicolon_count = sql_clean.count(";")
        if semicolon_count > 1:
            errors.append(
                "No se permiten múltiples statements SQL."
            )

        # 3️⃣ No comentarios
        if "--" in sql_clean or "/*" in sql_clean or "*/" in sql_clean:
            errors.append(
                "No se permiten comentarios en el SQL."
            )

        # 4️⃣ Palabras prohibidas
        for keyword in cls.FORBIDDEN_KEYWORDS:
            pattern = r"\b" + keyword + r"\b"
            if re.search(pattern, sql_upper):
                errors.append(
                    f"No se permite usar la palabra reservada prohibida: {keyword}."
                )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    # ==================================================
    # VALIDACIÓN ARQUITECTÓNICA POR NIVEL
    # ==================================================
    @classmethod
    def validate_level_sql(
        cls,
        sql: str,
        nivel: int,
        parametros_permitidos: list[str],
    ) -> dict:
        """
        Valida reglas arquitectónicas multinivel.

        Reglas:
        - Solo puede usar parámetros declarados en parametros.variables
        - No puede usar parámetros implícitos como :id_asiento
        - Nivel > 0 NO puede depender de parámetros derivados de otro nivel
        """

        errors = []

        if not sql:
            errors.append("El SQL no puede estar vacío.")
            return {"is_valid": False, "errors": errors}

        # Extraer parámetros usados en el SQL
        params_encontrados = re.findall(cls.PARAM_PATTERN, sql)

        # --------------------------------------------------
        # 1️⃣ Validar parámetros no declarados
        # --------------------------------------------------
        for param in params_encontrados:
            if param not in parametros_permitidos:
                errors.append(
                    f"El parámetro ':{param}' no está declarado en parametros.variables."
                )

        # --------------------------------------------------
        # 2️⃣ Regla crítica multinivel
        # --------------------------------------------------
        # Si es nivel > 0, no debe usar parámetros dinámicos
        # Solo se permiten los globales declarados
        if nivel > 0 and params_encontrados:
            for param in params_encontrados:
                if param not in parametros_permitidos:
                    errors.append(
                        f"El nivel {nivel} no puede depender de parámetros dinámicos como ':{param}'. "
                        "Los vínculos entre niveles deben resolverse en código, no en SQL."
                    )

        # --------------------------------------------------
        # 3️⃣ Bloquear patrón WHERE campo = :campo
        # si el parámetro parece un ID típico
        # --------------------------------------------------
        suspicious_patterns = [
            r"WHERE\s+.*=\s*:[a-zA-Z_][a-zA-Z0-9_]*"
        ]

        if nivel > 0:
            for pattern in suspicious_patterns:
                if re.search(pattern, sql, re.IGNORECASE):
                    errors.append(
                        "Un nivel secundario no puede filtrar por parámetro dinámico "
                        "(ej: WHERE campo = :id). "
                        "Debe traer el universo completo y agrupar en código."
                    )

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }