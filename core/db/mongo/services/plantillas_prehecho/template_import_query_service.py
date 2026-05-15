# core/db/mongo/services/plantillas_prehecho/template_import_query_service.py

from core.db.mongo.connection import (
    MongoConnectionFactory,
)


class TemplateImportQueryService:
    """
    Servicio MongoDB encargado
    de importar documentos
    de plantillas prehechas.
    """


    # =========================
    # Obtener colección
    # =========================
    @staticmethod
    def get_collection(
        *,
        company,
        collection_name: str,
    ):
        """
        Retorna colección MongoDB
        de la empresa.
        """

        if not collection_name:
            raise ValueError(
                "collection_name es requerido"
            )

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db[collection_name]


    # =========================
    # Insert many documents
    # =========================
    @staticmethod
    def insert_many_documents(
        *,
        company,
        collection_name: str,
        documents: list,
    ):
        """
        Inserta múltiples documentos
        preservando _id original.
        """

        if not isinstance(documents, list):
            raise ValueError(
                "documents debe ser lista"
            )

        if not documents:
            return []

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        result = collection.insert_many(
            documents
        )

        return result.inserted_ids
  


    # =========================
    # Delete all documents
    # =========================
    @staticmethod
    def delete_all_documents(
        *,
        company,
        collection_name: str,
    ):
        """
        Elimina todos los documentos
        de una colección.
        """

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        result = collection.delete_many({})

        return result.deleted_count


    # =========================
    # Count documents
    # =========================
    @staticmethod
    def count_documents(
        *,
        company,
        collection_name: str,
    ):
        """
        Cuenta documentos
        de una colección.
        """

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        return collection.count_documents({})
    
    # =========================
    # Obtener documentos
    # =========================
    @staticmethod
    def get_documents(
        *,
        company,
        collection_name: str,
        filters: dict | None = None,
    ):
        """
        Obtiene documentos
        de una colección.
        """

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        return list(
            collection.find(
                filters or {}
            )
        )

    # =========================
    # Actualizar documento
    # =========================
    @staticmethod
    def update_document(
        *,
        company,
        collection_name: str,
        document_id,
        update_data: dict,
    ):
        """
        Actualiza documento MongoDB.
        """

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        result = collection.update_one(
            {
                "_id": document_id
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
    # Delete document
    # =========================
    @staticmethod
    def delete_document(
        *,
        company,
        collection_name: str,
        document_id,
    ):
        """
        Elimina un documento.
        """

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
            )
        )

        result = collection.delete_one(
            {
                "_id": document_id
            }
        )

        return {
            "deleted_count": result.deleted_count,
        }

    # =========================
    # Upsert document
    # =========================
    @staticmethod
    def upsert_document(
        *,
        company,
        collection_name: str,
        document: dict,
    ):
        """
        Inserta o reemplaza documento
        usando _id como clave natural.
        """

        if "_id" not in document:
            raise ValueError(
                "document debe contener _id"
            )

        collection = (
            TemplateImportQueryService.get_collection(
                company=company,
                collection_name=collection_name,
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