# core/db/mongo/services/plantillas_prehecho/metadata_query_service.py

from core.db.mongo.connection import (
    MongoConnectionFactory,
)


class MetadataQueryService:
    """
    Servicio MongoDB para colección Metadata.
    """


    # =========================
    # Obtener colección
    # =========================
    @staticmethod
    def get_collection(company):
        """
        Retorna colección Metadata
        de la empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db["metadata"]
    
    # =========================
    # Obtener metadata
    # =========================
    @staticmethod
    def get_all_metadata(*,company,):
        """
        Retorna todos los documentos
        metadata existentes.
        """

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        return list(
            collection.find({})
        )
    
    # =========================
    # Reset aplicada metadata
    # =========================
    @staticmethod
    def reset_metadata_aplicada(*, company,):
        """
        Reinicia el estado aplicada
        de toda la metadata a "No".
        """

        collection = MetadataQueryService.get_collection(
            company
        )

        result = collection.update_many(
            {},
            {
                "$set": {
                    "aplicada": "No",
                }
            },
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }


    # =========================
    # Insert metadata
    # =========================
    @staticmethod
    def insert_metadata(
        *,
        company,
        document: dict,
    ):
        """
        Inserta documento metadata.
        """

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        result = collection.insert_one(
            document
        )

        return result.inserted_id

    # =========================
    # Insert many metadata
    # =========================
    @staticmethod
    def insert_many_metadata(
        *,
        company,
        documents: list,
    ):
        """
        Inserta múltiples documentos metadata.
        """

        if not documents:
            return []

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        result = collection.insert_many(
            documents
        )

        return result.inserted_ids
    

    # =========================
    # Upsert metadata
    # =========================
    @staticmethod
    def upsert_metadata(
        *,
        company,
        document: dict,
    ):
        """
        Inserta o reemplaza metadata
        usando _id como clave natural.
        """

        if "_id" not in document:
            raise ValueError(
                "document debe contener _id"
            )

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        result = collection.replace_one(
            {
                "_id": document["_id"]
            },
            document,
            upsert=True,
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": result.upserted_id,
        }
    

    # =========================
    # Update metadata
    # =========================
    @staticmethod
    def update_metadata(
        *,
        company,
        metadata_id,
        update_data: dict,
    ):
        """
        Actualiza documento metadata.
        """

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        result = collection.update_one(
            {
                "_id": metadata_id
            },
            {
                "$set": update_data
            }
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }

    # =========================
    # Delete metadata
    # =========================
    @staticmethod
    def delete_metadata(
        *,
        company,
        metadata_id,
    ):
        """
        Elimina documento metadata.
        """

        collection = (
            MetadataQueryService.get_collection(
                company
            )
        )

        result = collection.delete_one(
            {
                "_id": metadata_id
            }
        )

        return {
            "deleted_count": result.deleted_count,
        }