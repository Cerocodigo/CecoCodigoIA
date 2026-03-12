# core/db/mongo/services/provision_service.py
# ===========================================
# Provisionamiento MongoDB por empresa
# ===========================================

from core.db.mongo.connection import MongoConnectionFactory


class MongoProvisionService:
    """
    Servicio encargado de:
    - Inicializar base de datos MongoDB por empresa
    - Crear estructura mínima inicial

    MongoDB crea bases de datos de forma diferida,
    por lo que aquí forzamos su materialización.
    """

    @classmethod
    def provision_company_database(cls,*,mongo_uri: str,db_name: str):
        """
        Provisiona una base MongoDB para una empresa.

        - mongo_uri: proviene de MongoServer.uri
        - db_name: definido en create_company_view
        """

        client = MongoConnectionFactory.get_admin_client(mongo_uri)

        try:
            db = client[db_name]

            # =========================
            # Forzar creación de la base
            # =========================
            # MongoDB crea la DB cuando existe al menos
            # una colección con un documento.
            db["_init"].insert_one(
                {
                    "system": "CecoCodigoIA",
                    "status": "initialized"
                }
            )

        finally:
            client.close()
