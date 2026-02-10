# core/services/update_model_mysql_schema_service.py
# ==================================================
# Servicio de sincronización MongoDB → MySQL
# ==================================================

from core.db.mongo.services.models.model_query_service import (
    ModelQueryService,
)

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.ddl_service import MySQLDDLService
from core.db.mysql.services.dml_service import MySQLDMLService
from core.db.mysql.sql.sql_generator import SQLGenerator
from core.db.mysql.exceptions import MySQLServiceError


class UpdateModelMySQLSchemaService:
    """
    Servicio transversal encargado de sincronizar
    la estructura MySQL a partir de un modelo MongoDB.
    """

    # =========================
    # API pública
    # =========================

    @staticmethod
    def update_schema_for_model(*, company, model_id: str):
        """
        Punto de entrada único.

        - Obtiene el modelo desde MongoDB
        - Sincroniza la tabla MySQL asociada
        """

        # =========================
        # 1️⃣ Obtener modelo Mongo
        # =========================
        model = ModelQueryService.get_model_by_id(
            company=company,
            model_id=model_id,
        )

        if not model:
            raise ValueError("Modelo MongoDB no encontrado")

        table_name = model["tabla"]
        campos = model.get("campos", [])

        # =========================
        # 2️⃣ Infraestructura MySQL
        # =========================
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )

        executor = MySQLExecutor(connection)
        ddl = MySQLDDLService(executor)
        dml = MySQLDMLService(executor)

        # =========================
        # 3️⃣ Verificar si la tabla existe
        # =========================
        sql_exists = """
            SELECT COUNT(*) AS total
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
              AND table_name = %s
        """

        result = executor.fetch_one(sql_exists, (table_name,))
        table_exists = result["total"] == 1

        # =========================
        # 4️⃣ Convertir campos Mongo → SQL
        # =========================
        mongo_columns = {
            campo["nombre"]: mongo_field_to_sql(campo)
            for campo in campos
        }

        # =========================
        # 5️⃣ Crear tabla si no existe
        # =========================
        if not table_exists:
            sql, _ = SQLGenerator.create_table(
                table_name=table_name,
                columns=list(mongo_columns.values()),
            )
            ddl.create_table(sql)
            return

        # =========================
        # 6️⃣ Obtener columnas MySQL existentes
        # =========================
        sql_columns = """
            SELECT
                column_name,
                column_type,
                is_nullable,
                extra
            FROM information_schema.columns
            WHERE table_schema = DATABASE()
              AND table_name = %s
        """

        rows = executor.fetch_all(sql_columns, (table_name,))

        mysql_columns = {
            row["column_name"]: row
            for row in rows
        }

        # =========================
        # 7️⃣ Comparar y sincronizar
        # =========================

        # 7.1 ➕ Columnas nuevas
        for name, definition in mongo_columns.items():
            if name not in mysql_columns:
                sql, _ = SQLGenerator.add_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

        # 7.2 🔄 Columnas modificadas
        for name, definition in mongo_columns.items():
            if name in mysql_columns:
                sql, _ = SQLGenerator.modify_column(
                    table_name=table_name,
                    column_definition=definition,
                )
                ddl.alter_table(sql)

        # 7.3 ➖ Columnas sobrantes
        for name in mysql_columns.keys():
            if name not in mongo_columns:
                sql, _ = SQLGenerator.drop_column(
                    table_name=table_name,
                    column_name=name,
                )
                ddl.alter_table(sql)


# ==================================================
# Conversión Mongo → SQL
# ==================================================

SQL_TYPES = {
    "string": "VARCHAR(255)",
    "char": "CHAR(1)",
    "text": "TEXT",
    "int": "INT",
    "integer": "INT",
    "decimal": "DECIMAL(10,2)",
    "boolean": "TINYINT(1)",
    "date": "DATE",
    "datetime": "DATETIME",
    "time": "TIME",
    "fk": "INT",
}


def mongo_field_to_sql(campo: dict) -> str:
    """
    Convierte un campo del modelo MongoDB
    a definición SQL MySQL.
    """

    nombre = campo["nombre"]
    nombre_sql = f"`{nombre}`"

    tipo_base = campo.get("tipo_base")
    tipo_funcional = campo.get("tipo_funcional")

    sql_type = SQL_TYPES.get(tipo_base)
    if not sql_type:
        raise ValueError(f"Tipo SQL no soportado: {tipo_base}")

    requerido = campo.get("requerido", False)
    null_sql = "NOT NULL" if requerido else "NULL"

    extras = []

    if tipo_funcional == "NumeroSecuencial":
        extras.append("AUTO_INCREMENT")
        extras.append("PRIMARY KEY")
        null_sql = "NOT NULL"

    if tipo_funcional == "FechaCreacion":
        extras.append("DEFAULT CURRENT_TIMESTAMP")

    if tipo_funcional == "FechaActualizacion":
        extras.append(
            "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        )

    return " ".join([
        nombre_sql,
        sql_type,
        null_sql,
        *extras
    ]).strip()
