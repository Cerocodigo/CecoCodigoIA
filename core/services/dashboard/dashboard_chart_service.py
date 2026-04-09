# core/services/dashboard/dashboard_chart_service.py
# ==================================================
# Servicio para cargar charts del dashboard
# ==================================================

from decimal import Decimal

from core.db.mongo.services.dashboard.dashboard_query_service import (
    DashboardQueryService,
)

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService


class DashboardChartService:

    @staticmethod
    def cargar_charts(company):
        """
        Obtiene la configuración de charts desde MongoDB
        y ejecuta los SQL contra la base de datos de la empresa
        """

        # 1. Obtener charts activos desde Mongo
        charts = DashboardQueryService.get_dashboards_active(
            company=company,
            is_raw=False,
        )

        if not charts:
            return {
                "lista_charts": [],
                "valores_charts": {}
            }

        # 2. Ordenar
        charts.sort(key=lambda c: c.get("Orden", 1))

        # 3. Conexión (UNA sola vez)
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        valores_charts = {}

        try:
            for chart in charts:

                sql = chart.get("Sql")

                if not sql:
                    valores_charts[chart["id"]] = []
                    continue

                try:
                    rows = dml.fetch_all(sql)
                    rows = normalize_rows(rows)
                except Exception as e:
                    rows = []
                valores_charts[chart["id"]] = rows
        finally:
            try:
                connection.close()
            except Exception:
                pass

        return {
            "lista_charts": charts,
            "valores_charts": valores_charts
        }
    

    


def normalize_rows(rows):
    normalized = []

    for row in rows:
        new_row = {}
        for key, value in row.items():

            if isinstance(value, Decimal):
                new_row[key] = float(value)

            else:
                new_row[key] = value

        normalized.append(new_row)

    return normalized