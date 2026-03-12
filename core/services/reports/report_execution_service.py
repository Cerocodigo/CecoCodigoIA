# core/services/reports/report_execution_service.py

import re

from core.db.mongo.services.reports.report_query_service import (
    ReportQueryService,
)
from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService
from core.services.reports.report_sql_validator import (
    ReportSQLValidator,
)


class ParameterCompiler:

    PARAM_PATTERN = re.compile(r":([a-zA-Z_][a-zA-Z0-9_]*)")

    @classmethod
    def compile(cls, *, sql: str, parametros: dict | None):
        if not parametros:
            parametros = {}

        found_params = cls.PARAM_PATTERN.findall(sql)
        query_params = []

        for param_name in found_params:
            if param_name not in parametros:
                raise ValueError(f"Falta parámetro requerido ': {param_name}'")


        def replacement(match):
            param_name = match.group(1)
            query_params.append(parametros[param_name])
            return "%s"

        compiled_sql = cls.PARAM_PATTERN.sub(replacement, sql)

        return compiled_sql, tuple(query_params)


class ReportExecutionService:

    MAX_LEVEL0_ROWS = 1000

    @staticmethod
    def execute_level(*, company, report_id: str, nivel: int, parametros: dict):
        report = ReportQueryService.get_report_by_id(
            company=company,
            report_id=report_id,
        )

        if not report:
            return {
                "success": False,
                "data": None,
                "errors": ["Reporte no encontrado"],
            }

        niveles = report.get("niveles", [])

        nivel_config = next(
            (n for n in niveles if n["nivel"] == nivel),
            None,
        )

        if not nivel_config:
            return {
                "success": False,
                "data": None,
                "errors": ["Nivel no definido"],
            }

        sql_original = nivel_config["query"]

        validation = ReportSQLValidator.validate_sql(sql_original)

        if not validation["is_valid"]:
            return {
                "success": False,
                "data": None,
                "errors": validation["errors"],
            }

        # 👇 LIMIT automático en nivel 0
        if nivel == 0:
            sql_original = f"""
            SELECT * FROM (
                {sql_original}
            ) AS nivel0_subquery
            LIMIT {ReportExecutionService.MAX_LEVEL0_ROWS}
            """


        try:
            compiled_sql, query_params = ParameterCompiler.compile(
                sql=sql_original,
                parametros=parametros,
            )
        except ValueError as e:
            return {
                "success": False,
                "data": None,
                "errors": [str(e)],
            }
        
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            rows = dml.fetch_all(compiled_sql, query_params)
        finally:
            try:
                connection.close()
            except Exception:
                pass

        # 👇 Si es subnivel, agrupar por campo_padre
        vinculos = nivel_config.get("vinculos", {})
        campo_padre = vinculos.get("campo_padre")

        if campo_padre:
            grouped = {}
            for row in rows:
                key = row.get(campo_padre)
                grouped.setdefault(str(key), []).append(row)
            return {
                "success": True,
                "data": grouped,
                "errors": [],
            }

        return {
            "success": True,
            "data": rows,
            "errors": [],
        }