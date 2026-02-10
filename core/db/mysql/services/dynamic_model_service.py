# core/db/mysql/services/dynamic_model_service.py
# ===============================================
# Servicio orientado a modelos dinámicos MySQL
# ===============================================

from core.db.mysql.sql.sql_generator import SQLGenerator
from core.db.mysql.sql.sql_validator import SQLValidator
from core.db.mysql.services.ddl_service import MySQLDDLService
from core.db.mysql.services.dml_service import MySQLDMLService
from core.db.mysql.exceptions import MySQLServiceError


class DynamicModelService:
    """
    Servicio de alto nivel orientado a modelos dinámicos.

    Orquesta:
    - Generación de SQL
    - Validación de seguridad
    - Ejecución DDL / DML

    NO conoce:
    - MongoDB
    - Conexiones
    - Reglas de negocio
    """

    def __init__(
        self,
        *,
        ddl_service: MySQLDDLService,
        dml_service: MySQLDMLService,
    ):
        if not ddl_service or not dml_service:
            raise MySQLServiceError(
                "DDLService y DMLService son obligatorios"
            )

        self.ddl = ddl_service
        self.dml = dml_service

    # =========================
    # ESTRUCTURA (DDL)
    # =========================

    def create_table(self, model_descriptor: dict):
        """
        Crea la tabla asociada al modelo dinámico.
        """
        sql = SQLGenerator.create_table(model_descriptor)
        SQLValidator.validate(sql)
        return self.ddl.create_table(sql)

    def drop_table(self, model_descriptor: dict):
        """
        Elimina completamente la tabla del modelo dinámico.
        """
        sql = SQLGenerator.drop_table(model_descriptor)
        SQLValidator.validate(sql)
        return self.ddl.drop_table(sql)

    def add_columns(self, model_descriptor: dict, columns: list[dict]):
        """
        Agrega nuevas columnas a la tabla.

        columns: lista de descriptores de columna
        """
        sql_list = SQLGenerator.alter_add_columns(
            model_descriptor,
            columns,
        )

        for sql in sql_list:
            SQLValidator.validate(sql)
            self.ddl.alter_table(sql)

    def modify_columns(self, model_descriptor: dict, columns: list[dict]):
        """
        Modifica columnas existentes.
        """
        sql_list = SQLGenerator.alter_modify_columns(
            model_descriptor,
            columns,
        )

        for sql in sql_list:
            SQLValidator.validate(sql)
            self.ddl.alter_table(sql)

    def drop_columns(self, model_descriptor: dict, columns: list[str]):
        """
        Elimina columnas de la tabla.
        """
        sql_list = SQLGenerator.alter_drop_columns(
            model_descriptor,
            columns,
        )

        for sql in sql_list:
            SQLValidator.validate(sql)
            self.ddl.alter_table(sql)

    # =========================
    # DATOS (DML)
    # =========================

    def insert(self, model_descriptor: dict, data: dict) -> int:
        """
        Inserta un registro según el modelo dinámico.
        """
        sql, params = SQLGenerator.insert(model_descriptor, data)
        return self.dml.insert(sql, params)

    def update(self,model_descriptor: dict,data: dict,*,where: dict) -> int:
        """
        Actualiza registros según el modelo dinámico.
        """
        sql, params = SQLGenerator.update(
            model_descriptor,
            data,
            where=where,
        )
        return self.dml.update(sql, params)

    def delete(self, model_descriptor: dict, *, where: dict) -> int:
        """
        Elimina registros según el modelo dinámico.
        """
        sql, params = SQLGenerator.delete(
            model_descriptor,
            where=where,
        )
        return self.dml.delete(sql, params)

    def fetch_all(self,model_descriptor: dict,*,where: dict | None = None,) -> list[dict]:
        """
        Obtiene múltiples registros.
        """
        sql, params = SQLGenerator.select(
            model_descriptor,
            where=where,
        )
        return self.dml.fetch_all(sql, params)

    def fetch_one(self,model_descriptor: dict,*,where: dict,) -> dict | None:
        """
        Obtiene un solo registro.
        """
        sql, params = SQLGenerator.select(
            model_descriptor,
            where=where,
            limit=1,
        )
        return self.dml.fetch_one(sql, params)
