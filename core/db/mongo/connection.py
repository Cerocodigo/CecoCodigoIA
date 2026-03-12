# core/db/mongo/connection.py
# =========================
# Conexiones MongoDB
# =========================

from pymongo import MongoClient


class MongoConnectionFactory:
    """
    Factoría de conexiones MongoDB.
    NO contiene lógica de negocio.
    NO depende de Django ORM.
    """

    @staticmethod
    def get_admin_client(mongo_uri: str) -> MongoClient:
        """
        Cliente administrativo MongoDB.
        Usado SOLO para provisioning.
        """
        return MongoClient(mongo_uri)

    @staticmethod
    def get_company_client(mongo_uri: str, db_name: str):
        """
        Cliente MongoDB apuntando a la base de datos de una empresa.
        """
        client = MongoClient(mongo_uri)
        return client[db_name]
