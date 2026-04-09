# core/db/mongo/services/models/model_query_service.py
# ====================================================
# Servicio de lectura de modelos desde MongoDB
# Colección: modelos
# ====================================================
from datetime import datetime
from django.utils.text import slugify

from core.db.mongo.connection import MongoConnectionFactory


class ModelQueryService:
    """
    Servicio de lectura de modelos (entidades)
    definidos en MongoDB.

    Colección: modelos
    """

    @staticmethod
    def get_collection(company):
        """
        Devuelve la colección Mongo 'modelos'
        de la empresa.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name,
        )

        return db["modelos"]

    @staticmethod
    def get_models_for_module(*, company, module_id: str, is_raw: bool = False) -> list[dict]:
        """
        Devuelve todos los modelos activos
        asociados a un módulo.

        Ej:
        module_id = "clientes"
        """

        collection = ModelQueryService.get_collection(company)

        models = list(
            collection.find(
                {
                    "modulo": module_id,
                    "activo": True,
                }
            )
        )

        # Normalizamos _id a string
        if not is_raw:
            for model in models:
                model["id"] = str(model["_id"])

        return models
    
    def get_models_byId(*, company, module_id: str, is_raw: bool = False) -> list[dict]:
        """
        Devuelve todos los modelos activos
        asociados a un módulo.

        Ej:
        module_id = "clientes"
        """

        collection = ModelQueryService.get_collection(company)

        models = list(
            collection.find(
                {
                    "_id": module_id,
                    "activo": True,
                }
            )
        )

        # Normalizamos _id a string
        if not is_raw:
            for model in models:
                model["id"] = str(model["_id"])

        return models

    @staticmethod
    def get_models_for_module_rol(*, company, module_id: str, module_rol: str, is_raw: bool = False) -> list[dict]:
        """
        Devuelve todos los modelos activos
        asociados a un módulo y un rol específico.

        Ej:
        module_id = "clientes"
        module_rol = "cabecera"
        """

        collection = ModelQueryService.get_collection(company)

        models = list(
            collection.find(
                {
                    "modulo": module_id,
                    "rol": module_rol,
                    "activo": True,
                }
            )
        )

        # Normalizamos _id a string
        if not is_raw:
            for model in models:
                model["id"] = str(model["_id"])

        return models

    @staticmethod
    def get_model_by_id(*, company, model_id: str, is_raw: bool = False) -> dict | None:
        """
        Obtiene un modelo específico por su _id.
        """

        collection = ModelQueryService.get_collection(company)

        model = collection.find_one(
            {
                "_id": model_id,
                "activo": True,
            }
        )

        if model and not is_raw:
            model["id"] = str(model["_id"])

        return model
    
    @staticmethod
    def create_model(*,company,module_id: str,nombre: str | None = None,) -> dict:
        """
        Crea un modelo inicial asociado a un módulo,
        incluyendo automáticamente su campo PK.

        - _id: igual al module_id para simplificar
        - pk: id_<model_id>
        - campos: incluye el campo PK por defecto
        """

        collection = ModelQueryService.get_collection(company)

        model_id = module_id
        pk_name = f"id_{model_id}"

        if collection.find_one({"_id": model_id}):
            raise ValueError("Ya existe un modelo para este módulo")

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
            "_id": model_id,
            "activo": True,
            "tabla": model_id,
            "rol": "cabecera",
            "pk": pk_name,
            "campos": [pk_field],
            "modulo": module_id,
            "creado_en": datetime.utcnow(),
        }

        collection.insert_one(document)

        return document
