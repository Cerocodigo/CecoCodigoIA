# core/services/reports/report_persistence_service.py
# ==================================================
# Servicio de persistencia de reportes
# ==================================================

from datetime import datetime
from django.utils.text import slugify

from core.db.mongo.services.reports.report_query_service import (
    ReportQueryService,
)


class ReportPersistenceService:
    """
    Servicio responsable de:

    - Normalizar identificador
    - Aplicar metadata técnica
    - Manejar versionado inicial
    - Persistir en Mongo

    NO valida JSON.
    NO ejecuta SQL.
    """

    # ==================================================
    # API pública
    # ==================================================

    @staticmethod
    def create_report(
        *,
        company,
        report_definition: dict,
        created_by: str | None = None,
    ) -> dict:
        """
        Persiste un reporte ya validado.

        Retorna el documento final persistido.
        """

        document = ReportPersistenceService._build_document(
            report_definition=report_definition,
            created_by=created_by,
        )

        ReportQueryService.insert_one(
            company=company,
            document=document,
        )

        return document

    # ==================================================
    # Internals
    # ==================================================

    @staticmethod
    def _build_document(
        *,
        report_definition: dict,
        created_by: str | None,
    ) -> dict:
        """
        Construye documento final listo para Mongo.
        """

        now = datetime.utcnow()

        # Normalizamos _id desde nombre
        report_id = slugify(
            report_definition["nombre"]
        ).replace("-", "_")

        return {
            "_id": report_id,
            "nombre": report_definition["nombre"],
            "descripcion": report_definition["descripcion"],
            "modulos": report_definition["modulos"],
            "exportable": report_definition["exportable"],
            "parametros": report_definition["parametros"],
            "niveles": report_definition["niveles"],

            # 🔹 Control técnico
            "activo": True,
            "version": 1,
            "creado_en": now,
            "actualizado_en": now,
            "creado_por": created_by,
        }