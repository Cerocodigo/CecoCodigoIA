# core/db/mysql/sql/sql_generator.py
# =================================
# Generador de SQL (DDL + DML)
# =================================
# - NO ejecuta SQL
# - NO valida seguridad
# - NO conoce conexiones
# - SOLO genera (sql, params)
# =================================


class SQLGenerator:
    """
    Generador de sentencias SQL parametrizadas.

    Este módulo:
    - Genera SQL como string
    - Retorna parámetros separados
    - No ejecuta
    - No valida reglas de seguridad
    """

    # =========================
    # DDL
    # =========================

    @staticmethod
    def create_table(*,table_name: str,columns: list[str],engine: str = "InnoDB",charset: str = "utf8mb4",) -> tuple[str, tuple]:
        """
        Genera SQL para CREATE TABLE.

        columns:
            Lista de definiciones SQL ya formateadas
            ej: ["id INT PRIMARY KEY", "name VARCHAR(100) NOT NULL"]
        """

        columns_sql = ",\n    ".join(columns)

        sql = f"""
        CREATE TABLE {table_name} (
            {columns_sql}
        ) ENGINE={engine}
          DEFAULT CHARSET={charset}
        """

        return sql.strip(), ()

    @staticmethod
    def drop_table(*, table_name: str) -> tuple[str, tuple]:
        sql = f"DROP TABLE IF EXISTS {table_name}"
        return sql, ()

    @staticmethod
    def add_column(*,table_name: str,column_definition: str,) -> tuple[str, tuple]:
        sql = f"ALTER TABLE {table_name} ADD COLUMN {column_definition}"
        return sql, ()

    @staticmethod
    def modify_column(*,table_name: str,column_definition: str,) -> tuple[str, tuple]:
        sql = f"ALTER TABLE {table_name} MODIFY COLUMN {column_definition}"
        return sql, ()

    @staticmethod
    def drop_column(*,table_name: str,column_name: str,) -> tuple[str, tuple]:
        sql = f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
        return sql, ()

    # =========================
    # DML
    # =========================

    @staticmethod
    def insert(*,table_name: str,data: dict,) -> tuple[str, tuple]:
        """
        INSERT parametrizado.
        """

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s"] * len(data))
        params = tuple(data.values())

        sql = f"""
        INSERT INTO {table_name} ({columns})
        VALUES ({placeholders})
        """

        return sql.strip(), params

    @staticmethod
    def update(*,table_name: str,data: dict,where: dict,) -> tuple[str, tuple]:
        """
        UPDATE parametrizado con WHERE obligatorio.
        """

        set_clause = ", ".join([f"{k} = %s" for k in data.keys()])
        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])

        params = tuple(data.values()) + tuple(where.values())

        sql = f"""
        UPDATE {table_name}
        SET {set_clause}
        WHERE {where_clause}
        """

        return sql.strip(), params

    @staticmethod
    def delete(*,table_name: str,where: dict,) -> tuple[str, tuple]:
        """
        DELETE con WHERE obligatorio.
        """

        where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
        params = tuple(where.values())

        sql = f"""
        DELETE FROM {table_name}
        WHERE {where_clause}
        """

        return sql.strip(), params

    @staticmethod
    def select(*,table_name: str,columns: list[str],where: dict | None = None,limit: int | None = None,) -> tuple[str, tuple]:
        """
        SELECT simple y controlado.
        """
        cols = ", ".join(columns)
        params: tuple = ()
        sql = f"SELECT {cols} FROM {table_name}"
        if where:
            where_clause = " AND ".join([f"{k} = %s" for k in where.keys()])
            sql += f" WHERE {where_clause}"
            params = tuple(where.values())
        if limit is not None:
            sql += " LIMIT %s"
            params += (limit,)
        return sql, params
        