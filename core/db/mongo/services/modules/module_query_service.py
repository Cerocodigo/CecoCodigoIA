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
    def create_module(company, nombre, descripcion="", uso="medio", entidades=[]):
        """
        Crea un nuevo módulo en la colección 'modulos'
        """

        collection = ModuleQueryService.get_collection(company)

        module_id = slugify(nombre)
        # reemplazamos - por _ para evitar problemas en JS
        module_id = module_id.replace("-", "_")

        if collection.find_one({"_id": module_id}):
            raise ValueError("Ya existe un módulo con ese nombre")

        ### ia interpreta el decricpción como instrucciones para configurar el módulo, por eso lo hacemos obligatorio y no permitimos que sea vacío

        
        document = {
            "_id": module_id,
            "nombre": nombre,
            "descripcion": descripcion,
            "uso": uso,
            "activo": True,
            "entidades": entidades,
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

    # =========================
    # Update module
    # =========================
    @staticmethod
    def update_module(
        *,
        company,
        module_id: str,
        update_data: dict,
    ):
        """
        Actualiza parcialmente un módulo.
        """

        collection = ModuleQueryService.get_collection(
            company
        )

        result = collection.update_one(
            {
                "_id": module_id,
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
    # Delete module
    # =========================
    @staticmethod
    def delete_module(
        *,
        company,
        module_id: str,
    ):
        """
        Elimina un módulo.
        """

        collection = ModuleQueryService.get_collection(
            company
        )

        result = collection.delete_one(
            {
                "_id": module_id,
            }
        )

        return {
            "deleted_count": result.deleted_count,
        }

    # =========================
    # Upsert module
    # =========================
    @staticmethod
    def upsert_module(
        *,
        company,
        document: dict,
    ):
        """
        Inserta o reemplaza módulo
        usando _id como clave natural.
        """

        if "_id" not in document:
            raise ValueError(
                "document debe contener _id"
            )

        collection = ModuleQueryService.get_collection(
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