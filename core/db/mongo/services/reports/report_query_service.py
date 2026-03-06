# core/db/mongo/services/reports/report_query_service.py
# ======================================================
# Servicio de acceso MongoDB para Reportes
# Colección: reportes
# ======================================================

from datetime import datetime

from core.db.mongo.connection import MongoConnectionFactory


class ReportQueryService:
    """
    Servicio de lectura y escritura de reportes en MongoDB.

    Colección: reportes

    NO contiene lógica de negocio.
    NO valida estructura.
    NO ejecuta SQL.
    """

    # ==================================================
    # Collection resolver
    # ==================================================

    @staticmethod
    def get_collection(company):
        """
        Devuelve la colección Mongo 'reportes' de la empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db["reportes"]

    # ==================================================
    # Create
    # ==================================================

    @staticmethod
    def insert_one(*, company, document: dict):
        """
        Inserta un nuevo reporte.
        """

        collection = ReportQueryService.get_collection(company)
        collection.insert_one(document)

    # ==================================================
    # Read
    # ==================================================

    @staticmethod
    def get_report_by_id(*, company, report_id: str) -> dict | None:
        """
        Obtiene un reporte activo por su _id.
        """

        collection = ReportQueryService.get_collection(company)
        report = collection.find_one(
            {
                "_id": report_id,
                "activo": True,
            }
        )

        if report:
            report["id"] = str(report["_id"])

        return report

    @staticmethod
    def get_active_reports(company) -> list[dict]:
        """
        Devuelve todos los reportes activos.
        """

        collection = ReportQueryService.get_collection(company)

        reports = list(
            collection.find(
                {"activo": True}
            )
        )

        for r in reports:
            r["id"] = str(r["_id"])

        return reports

    @staticmethod
    def get_reports_by_module(*, company, module_id: str) -> list[dict]:
        """
        Devuelve reportes activos asociados a un módulo.
        """

        collection = ReportQueryService.get_collection(company)

        reports = list(
            collection.find(
                {
                    "modulos": module_id,
                    "activo": True,
                }
            )
        )

        for r in reports:
            r["id"] = str(r["_id"])

        return reports

    # ==================================================
    # Update
    # ==================================================

    @staticmethod
    def update_report(
        *,
        company,
        report_id: str,
        updated_fields: dict,
    ):
        """
        Actualiza campos del reporte.
        """

        collection = ReportQueryService.get_collection(company)

        updated_fields["actualizado_en"] = datetime.utcnow()

        collection.update_one(
            {"_id": report_id},
            {"$set": updated_fields},
        )

    # ==================================================
    # Soft Delete
    # ==================================================

    @staticmethod
    def deactivate_report(
        *,
        company,
        report_id: str,
    ):
        """
        Desactiva un reporte (soft delete).
        """

        collection = ReportQueryService.get_collection(company)

        collection.update_one(
            {"_id": report_id},
            {
                "$set": {
                    "activo": False,
                    "actualizado_en": datetime.utcnow(),
                }
            },
        )