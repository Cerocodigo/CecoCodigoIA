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

    @staticmethod
    def update_module(company, module_id, nombre=None, descripcion=None, uso=None, activo=None, entidades=None):
        """
        Modifica un módulo existente en la colección 'modulos'
        """

        collection = ModuleQueryService.get_collection(company)

        module = collection.find_one({"_id": module_id})
        if not module:
            raise ValueError("El módulo no existe")

        update_fields = {}

        # Si se cambia el nombre, actualizamos también entidades
        if nombre and nombre != module.get("nombre"):
            new_module_id = slugify(nombre).replace("-", "_")

            # Validar que no exista otro con ese ID
            if collection.find_one({"_id": new_module_id}):
                raise ValueError("Ya existe un módulo con ese nombre")

            update_fields["nombre"] = nombre
            update_fields["entidades"] = entidades

            # IMPORTANTE: cambiar _id implica crear nuevo doc y borrar el anterior
            new_document = {**module, **update_fields}
            new_document["_id"] = new_module_id

            collection.insert_one(new_document)
            collection.delete_one({"_id": module_id})

            return new_document

        # Campos normales
        if descripcion is not None:
            if descripcion.strip() == "":
                raise ValueError("La descripción no puede estar vacía")
            update_fields["descripcion"] = descripcion

        if uso is not None:
            update_fields["uso"] = uso

        if activo is not None:
            update_fields["activo"] = activo

        if not update_fields:
            return module  # no hay cambios

        collection.update_one(
            {"_id": module_id},
            {"$set": update_fields}
        )

        return collection.find_one({"_id": module_id})



    @staticmethod
    def update_module_entidades(company, module_id, entidades):
        """
        Actualiza únicamente el campo 'entidades' de un módulo
        """

        collection = ModuleQueryService.get_collection(company)

        module = collection.find_one({"_id": module_id})
        if not module:
            raise ValueError("El módulo no existe")

        # Validación
        if not isinstance(entidades, list) or not entidades:
            raise ValueError("entidades debe ser una lista no vacía")

        # Limpieza (recomendado)
        entidades_limpias = list({
            str(e).strip()
            for e in entidades
            if str(e).strip()
        })

        if not entidades_limpias:
            raise ValueError("entidades no contiene valores válidos")

        # Update
        collection.update_one(
            {"_id": module_id},
            {"$set": {"entidades": entidades_limpias}}
        )

        return collection.find_one({"_id": module_id})
    

    @staticmethod
    def delete_module(company, module_id):
        """
        Elimina un módulo de la colección 'modulos'
        """

        collection = ModuleQueryService.get_collection(company)

        module = collection.find_one({"_id": module_id})
        if not module:
            raise ValueError("El módulo no existe")

        result = collection.delete_one({"_id": module_id})

        if result.deleted_count == 0:
            raise RuntimeError("No se pudo eliminar el módulo")

        return {
            "deleted": True,
            "module_id": module_id
        }