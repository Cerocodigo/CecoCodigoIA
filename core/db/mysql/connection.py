# core/db/mysql/connection.py
# =========================
# Conexiones MySQL / MariaDB
# =========================

import pymysql


class MySQLConnectionFactory:
    """
    Factoría de conexiones MySQL.
    NO contiene lógica de negocio.
    NO depende de Django ORM.
    """

    @staticmethod
    def get_root_connection(host: str,port: int,username: str,password: str):
        """
        Conexión administrativa contra un servidor MySQL.
        Usada SOLO para provisioning.
        """
        return pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )

    @staticmethod
    def get_company_connection(host: str,port: int,db_name: str,db_user: str,db_password: str):
        """
        Conexión operativa por empresa.
        """
        return pymysql.connect(
            host=host,
            port=port,
            user=db_user,
            password=db_password,
            database=db_name,
            charset="utf8mb4",
            autocommit=True,
            cursorclass=pymysql.cursors.DictCursor,
        )
