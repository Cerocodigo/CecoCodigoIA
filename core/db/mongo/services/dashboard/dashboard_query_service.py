# core/db/mongo/services/dashboard/dashboard_query_service.py
# ====================================================
# Servicio de lectura de dashboards desde MongoDB
# Colección: dashboards
# ====================================================
from datetime import datetime
from django.utils.text import slugify

from core.db.mongo.connection import MongoConnectionFactory


class DashboardQueryService:
    """
    Servicio de lectura de dashboards
    definidos en MongoDB.

    Colección: dashboard
    """

    @staticmethod
    def get_collection(company):
        """
        Devuelve la colección Mongo 'dashboard'
        de la empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db["dashboard"]

    @staticmethod
    def get_dashboards_active(*, company, is_raw: bool = False) -> list[dict]:
        """
        Devuelve todos los dashboards activos.
        """

        collection = DashboardQueryService.get_collection(company)

        dashboards = list(
            collection.find(
                {
                    "Activo": True,
                }
            )
        )

        # Normalizamos _id a string
        if not is_raw:
            for dashboard in dashboards:
                dashboard["id"] = str(dashboard["_id"])

        return dashboards


    @staticmethod
    def get_dashboard_by_id(*, company, dashboard_id: str, is_raw: bool = False) -> dict | None:
        """
        Obtiene un dashboard específico por su _id.
        """

        collection = DashboardQueryService.get_collection(company)

        dashboard = collection.find_one(
            {
                "_id": dashboard_id,
                "Activo": True,
            }
        )

        if dashboard and not is_raw:
            dashboard["id"] = str(dashboard["_id"])

        return dashboard
    
    ##revisar y teminar
    @staticmethod
    def create_dashboard(*,company,module_id: str,nombre: str | None = None,) -> dict:
        """
        Crea un dashboard inicial asociado a un módulo,
        incluyendo automáticamente su campo PK.

        - _id: igual al module_id para simplificar
        - pk: id_<model_id>
        - campos: incluye el campo PK por defecto
        """

        collection = DashboardQueryService.get_collection(company)

        dashboard_id = module_id
        pk_name = f"id_{dashboard_id}"

        if collection.find_one({"_id": dashboard_id}):
            raise ValueError("Ya existe un dashboard para este módulo")

        pk_field = {
            "nombre": pk_name,
            "tipo_base": "int",
            "tipo_funcional": "NumeroSecuencial",
            "editable": False,
            "requerido": True,
            "uso": {
                "participa_en": ["identidad"]
            },
            "gap": 10,
            "area": "main",
        }

        document = {
            "_id": module_id,
            "activo": True,
            "tabla": module_id,
            "rol": "cabecera",
            "pk": pk_name,
            "campos": [pk_field],
            "modulo": module_id,
            "creado_en": datetime.utcnow(),
        }

        collection.insert_one(document)

        return document

    ##revisar y teminar
    @staticmethod
    def update_dashboard(*,company,module_id: str,datos_actualizados: dict) -> dict:
        """
        Actualiza un dashboard existente.
        """

        collection = DashboardQueryService.get_collection(company)

        result = collection.update_one(
            {"_id": module_id},
            {"$set": datos_actualizados}
        )

        if result.matched_count == 0:
            raise ValueError("No se encontró el dashboard a actualizar")

        return datos_actualizados
    

    ##revisar y teminar
    @staticmethod
    def delete_dashboard(*,company,module_id: str) -> dict:
        """
        Elimina un dashboard existente.
        """

        collection = DashboardQueryService.get_collection(company)

        result = collection.delete_one(
            {"_id": module_id}
        )

        if result.deleted_count == 0:
            raise ValueError("No se encontró el dashboard a eliminar")

        return {"message": "Dashboard eliminado correctamente"}