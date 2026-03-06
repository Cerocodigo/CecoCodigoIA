# core/services/reports/report_json_validator.py
# ==================================================
# Validador estructural de JSON de Reportes IA
# ==================================================

from core.services.reports.report_sql_validator import (
    ReportSQLValidator,
)


class ReportJSONValidator:
    """
    Valida estructura completa del reporte generado por IA.

    Responsabilidades:
    - Validar estructura general
    - Validar existencia de nivel 0
    - Validar secuencia de niveles (0..n sin saltos)
    - Validar contrato de vínculo jerárquico
    - Validar SQL por nivel
    - Acumular TODOS los errores detectados

    NO persiste datos.
    NO ejecuta SQL.
    """

    # ==================================================
    # API pública
    # ==================================================

    @classmethod
    def validate(cls, report_definition: dict) -> dict:
        """
        Valida completamente un reporte IA.

        Devuelve:
        {
            "is_valid": bool,
            "errors": list[str]
        }
        """

        errors: list[str] = []

        if not isinstance(report_definition, dict):
            return {
                "is_valid": False,
                "errors": ["El reporte debe ser un objeto JSON válido."],
            }

        cls._validate_general_structure(report_definition, errors)
        cls._validate_niveles(report_definition, errors)

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
        }

    # ==================================================
    # Validación estructura general
    # ==================================================

    @staticmethod
    def _validate_general_structure(report: dict, errors: list[str]):

        required_fields = [
            "nombre",
            "descripcion",
            "modulos",
            "exportable",
            "parametros",
            "niveles",
        ]

        for field in required_fields:
            if field not in report:
                errors.append(f"Falta el campo obligatorio '{field}'.")

        # ------------------------------
        # modulos
        # ------------------------------
        modulos = report.get("modulos")
        if not isinstance(modulos, list):
            errors.append("'modulos' debe ser una lista.")
        else:
            if len(modulos) == 0:
                errors.append("'modulos' no puede estar vacío.")
            else:
                for m in modulos:
                    if not isinstance(m, str) or not m.strip():
                        errors.append(
                            "Todos los elementos de 'modulos' deben ser strings válidos."
                        )

        # ------------------------------
        # exportable
        # ------------------------------
        exportable = report.get("exportable", {})
        if not isinstance(exportable, dict):
            errors.append("El campo 'exportable' debe ser objeto.")
        else:
            for key in ["pdf", "excel"]:
                if key not in exportable:
                    errors.append(f"'exportable.{key}' es obligatorio.")
                elif not isinstance(exportable.get(key), bool):
                    errors.append(
                        f"'exportable.{key}' debe ser booleano."
                    )

        # ------------------------------
        # parametros
        # ------------------------------
        parametros = report.get("parametros", {})
        if not isinstance(parametros, dict):
            errors.append("El campo 'parametros' debe ser objeto.")
        else:
            if not isinstance(parametros.get("variables", []), list):
                errors.append("'parametros.variables' debe ser lista.")
            if not isinstance(parametros.get("referencias", []), list):
                errors.append("'parametros.referencias' debe ser lista.")

        # ------------------------------
        # niveles
        # ------------------------------
        niveles = report.get("niveles")
        if not isinstance(niveles, list):
            errors.append("'niveles' debe ser una lista.")

    # ==================================================
    # Validación niveles jerárquicos
    # ==================================================

    @classmethod
    def _validate_niveles(cls, report: dict, errors: list[str]):

        niveles = report.get("niveles", [])

        if not niveles:
            errors.append("Debe existir al menos el nivel 0.")
            return

        if not isinstance(niveles, list):
            return

        niveles_ordenados = sorted(
            niveles,
            key=lambda x: x.get("nivel", -1)
        )

        expected_level = 0

        for nivel_obj in niveles_ordenados:
            nivel_num = nivel_obj.get("nivel")

            if nivel_num != expected_level:
                errors.append(
                    f"Los niveles deben ser secuenciales sin saltos. Se esperaba nivel {expected_level}."
                )
                expected_level = nivel_num

            expected_level += 1

        total_niveles = len(niveles_ordenados)

        for index, nivel in enumerate(niveles_ordenados):

            nivel_num = nivel.get("nivel")

            if nivel_num is None:
                errors.append("Cada nivel debe tener campo 'nivel'.")
                continue

            if "query" not in nivel:
                errors.append(
                    f"Nivel {nivel_num}: falta campo obligatorio 'query'."
                )

            if "columnas" not in nivel:
                errors.append(
                    f"Nivel {nivel_num}: falta campo obligatorio 'columnas'."
                )

            if "totales" not in nivel:
                errors.append(
                    f"Nivel {nivel_num}: falta campo obligatorio 'totales'."
                )

            if not isinstance(nivel.get("columnas", []), list):
                errors.append(
                    f"Nivel {nivel_num}: 'columnas' debe ser lista."
                )

            if not isinstance(nivel.get("totales", []), list):
                errors.append(
                    f"Nivel {nivel_num}: 'totales' debe ser lista."
                )

            sql = nivel.get("query", "")
            sql_result = ReportSQLValidator.validate_sql(sql)

            if not sql_result["is_valid"]:
                for sql_error in sql_result["errors"]:
                    errors.append(
                        f"Nivel {nivel_num}: {sql_error}"
                    )

            cls._validate_vinculos(
                nivel=nivel,
                nivel_index=index,
                total_niveles=total_niveles,
                errors=errors,
            )

    # ==================================================
    # Validación contrato de vínculos
    # ==================================================

    @staticmethod
    def _validate_vinculos(
        *,
        nivel: dict,
        nivel_index: int,
        total_niveles: int,
        errors: list[str],
    ):

        nivel_num = nivel.get("nivel")
        sql = nivel.get("query", "")
        sql_upper = sql.upper()

        has_vinculo_hijo = "VINCULO_HIJO" in sql_upper
        has_vinculo_padre = "VINCULO_PADRE" in sql_upper

        if total_niveles == 1:
            if has_vinculo_hijo:
                errors.append(
                    "Nivel 0 no debe tener 'VINCULO_HIJO' porque no existe nivel siguiente."
                )
            if has_vinculo_padre:
                errors.append(
                    "Nivel 0 no debe tener 'VINCULO_PADRE'."
                )
            return

        if nivel_index == 0:
            if not has_vinculo_hijo:
                errors.append(
                    "Nivel 0 debe incluir columna 'VINCULO_HIJO' para enlazar con nivel 1."
                )
            if has_vinculo_padre:
                errors.append(
                    "Nivel 0 no debe incluir 'VINCULO_PADRE'."
                )
            return

        if nivel_index == total_niveles - 1:
            if not has_vinculo_padre:
                errors.append(
                    f"Nivel {nivel_num} debe incluir columna 'VINCULO_PADRE' para enlazar con el nivel anterior."
                )
            if has_vinculo_hijo:
                errors.append(
                    f"Nivel {nivel_num} no debe incluir 'VINCULO_HIJO' porque es el último nivel."
                )
            return

        if not has_vinculo_padre:
            errors.append(
                f"Nivel {nivel_num} debe incluir 'VINCULO_PADRE'."
            )

        if not has_vinculo_hijo:
            errors.append(
                f"Nivel {nivel_num} debe incluir 'VINCULO_HIJO'."
            )