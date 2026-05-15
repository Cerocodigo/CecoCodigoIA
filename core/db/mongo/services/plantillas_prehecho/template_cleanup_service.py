# core/db/mongo/services/plantillas_prehecho/template_cleanup_service.py

from core.db.mongo.connection import (
    MongoConnectionFactory,
)


class TemplateCleanupService:
    """
    Servicio encargado de limpiar
    las colecciones MongoDB de una empresa
    antes de aplicar una plantilla prehecha.
    """

    # =========================
    # Colecciones protegidas
    # =========================
    PROTECTED_COLLECTIONS = [
        "metadata",
    ]


    # =========================
    # Obtener DB
    # =========================
    @staticmethod
    def get_db(company):
        """
        Retorna DB Mongo empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        return MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )


    # =========================
    # Obtener colecciones
    # =========================
    @staticmethod
    def get_all_collections(company):
        """
        Retorna todas las colecciones.
        """

        db = (
            TemplateCleanupService.get_db(
                company
            )
        )

        return db.list_collection_names()


    # =========================
    # Obtener eliminables
    # =========================
    @staticmethod
    def get_deletable_collections(
        company
    ):
        """
        Retorna colecciones eliminables.
        """

        collections = (
            TemplateCleanupService.get_all_collections(
                company
            )
        )

        deletable = []

        for collection_name in collections:

            # =========================
            # Proteger metadata
            # =========================
            if (collection_name.lower() in TemplateCleanupService.PROTECTED_COLLECTIONS):
                continue

            # =========================
            # Ignorar system.*
            # =========================
            if collection_name.startswith("system."):
                continue

            deletable.append(collection_name)

        return deletable


    # =========================
    # Eliminar colección
    # =========================
    @staticmethod
    def drop_collection(
        *,
        company,
        collection_name: str,
    ):
        """
        Elimina colección MongoDB.
        """

        db = (
            TemplateCleanupService.get_db(
                company
            )
        )

        db.drop_collection(
            collection_name
        )


    # =========================
    # Cleanup completo
    # =========================
    @staticmethod
    def cleanup_company_database(
        *,
        company,
    ):
        """
        Elimina todas las colecciones
        permitidas.
        """

        deletable_collections = TemplateCleanupService.get_deletable_collections(
            company
        )

        deleted = []

        for collection_name in deletable_collections:

            TemplateCleanupService.drop_collection(
                company=company,
                collection_name=collection_name,
            )

            deleted.append(
                collection_name
            )

        return {
            "deleted_collections": deleted,
            "total_deleted": len(deleted),
        }