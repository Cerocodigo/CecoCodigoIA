from datetime import datetime
from django.utils.text import slugify

from core.db.mongo.connection import MongoConnectionFactory


class ModuleQueryService:
    """
    Servicio de lectura y escritura de módulos en MongoDB
    Colección: modulos
    """

    @staticmethod
    def get_collection(company):
        """
        Devuelve la colección Mongo 'modulos' de la empresa.
        Crea la conexión bajo demanda usando los metadatos de Company.
        """

        mongo_uri = company.mongo_server.uri
        db_name = company.mongo_db_name

        db = MongoConnectionFactory.get_company_client(
            mongo_uri=mongo_uri,
            db_name=db_name
        )

        return db["modulos"]

    @staticmethod
    def get_active_modules(company):
        """
        Devuelve todos los módulos activos
        Normaliza el identificador para consumo en templates (id en lugar de _id)
        """
        collection = ModuleQueryService.get_collection(company)

        modules = list(collection.find({"activo": True}))

        for m in modules:
            m["id"] = str(m["_id"])

        return modules

    @staticmethod
    def get_module_by_id(*, company, module_id: str) -> dict | None:
        """
        Obtiene un módulo activo por su _id
        """
        collection = ModuleQueryService.get_collection(company)

        module = collection.find_one(
            {
                "_id": module_id,
                "activo": True,
            }
        )

        if module:
            module["id"] = str(module["_id"])

        return module

    @staticmethod
    def create_module(company, nombre, descripcion="", uso="medio"):
        """
        Crea un nuevo módulo en la colección 'modulos'
        """

        collection = ModuleQueryService.get_collection(company)

        module_id = slugify(nombre)
        # reemplazamos - por _ para evitar problemas en JS
        module_id = module_id.replace("-", "_")

        if collection.find_one({"_id": module_id}):
            raise ValueError("Ya existe un módulo con ese nombre")

        document = {
            "_id": module_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "uso": uso,
            "activo": True,
            "entidades": [nombre],
            "creado_en": datetime.utcnow(),
            "prompt_config": {
                "enabled": True,
                "label": "Instrucciones de configuración",
                "descripcion": (
                    "Describe cambios estructurales o de proceso "
                    "para este módulo"
                ),
            },
        }

        collection.insert_one(document)

        return document

