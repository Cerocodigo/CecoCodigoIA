# core/db/mongo/services/pdf_templates/pdf_template_query_service.py
# ================================================================
# Servicio de lectura de plantillas PDF desde MongoDB
# Colección: plantillas_pdf
# ================================================================

from core.db.mongo.connection import MongoConnectionFactory


class PDFTemplateQueryService:
    """
    Servicio de lectura de plantillas PDF
    almacenadas en MongoDB.

    Colección: plantillas_pdf
    """

    @staticmethod
    def get_collection(company):
        """
        Devuelve la colección Mongo 'plantillas_pdf'
        de la empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db["plantillas_pdf"]

    @staticmethod
    def get_pdf_template_by_id(*, company, template_id: str, is_raw: bool = False) -> dict | None:
        """
        Obtiene una plantilla PDF específica por su _id.
        """

        collection = PDFTemplateQueryService.get_collection(company)

        template = collection.find_one(
            {
                "_id": template_id,
                "activo": True,
            }
        )
        if template and not is_raw:
            template["id"] = str(template["_id"])

        return template
    
    @staticmethod
    def get_pdf_templates_by_module(*, company, module_id: str, is_raw: bool = False) -> list[dict]:
        """
        Devuelve todas las plantillas PDF activas
        asociadas a un módulo.
        """

        collection = PDFTemplateQueryService.get_collection(company)

        templates = list(
            collection.find(
                {
                    "modulo": module_id,
                    "activo": True,
                }
            )
        )

        if not is_raw:
            for temp in templates:
                temp["id"] = str(temp["_id"])

        return templates
    
    # =========================
    # Update PDF template
    # =========================
    @staticmethod
    def update_pdf_template(
        *,
        company,
        template_id: str,
        update_data: dict,
    ):
        """
        Actualiza una plantilla PDF.
        """

        collection = PDFTemplateQueryService.get_collection(
            company
        )

        result = collection.update_one(
            {
                "_id": template_id,
            },
            {
                "$set": update_data,
            },
        )

        return {
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
        }

    # =========================
    # Delete PDF template
    # =========================
    @staticmethod
    def delete_pdf_template(
        *,
        company,
        template_id: str,
    ):
        """
        Elimina plantilla PDF.
        """

        collection = PDFTemplateQueryService.get_collection(
            company
        )

        result = collection.delete_one(
            {
                "_id": template_id,
            }
        )

        return {
            "deleted_count": result.deleted_count,
        }

    # =========================
    # Upsert PDF template
    # =========================
    @staticmethod
    def upsert_pdf_template(
        *,
        company,
        document: dict,
    ):
        """
        Inserta o reemplaza plantilla PDF
        usando _id como clave natural.
        """

        if "_id" not in document:
            raise ValueError(
                "document debe contener _id"
            )

        collection = PDFTemplateQueryService.get_collection(
            company
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