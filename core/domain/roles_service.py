# OBSOLETO TEMPORALMENTE: Aún no se implementa, se migró a MongoDB para que funcione con el nuevo esquema de roles y permisos cuando esté listo.

from datetime import datetime
from bson import ObjectId

from core.mongo.collections import MongoCollections
from core.mongo.contracts.role_schema import role_schema


class RolesService:
    """
    Servicio central para manejo de roles por empresa.
    """

    @staticmethod
    def create_default_roles(company_id: ObjectId) -> ObjectId:
        """
        Crea los roles base de una empresa nueva.
        Retorna el ID del rol admin.
        """

        admin_role = role_schema(
            company_id=company_id,
            name="Administrador",
            slug="admin",
            permissions=[
                "users.view", "users.create", "users.update", "users.delete",
                "companies.update", "companies.invite",
                "modules.view", "modules.create", "modules.update", "modules.delete",
                "models.view", "models.create", "models.update", "models.delete",
            ],
            is_system=True
        )

        manager_role = role_schema(
            company_id=company_id,
            name="Manager",
            slug="manager",
            permissions=[
                "users.view",
                "modules.view", "modules.create", "modules.update",
                "models.view", "models.create", "models.update",
            ],
            is_system=True
        )

        user_role = role_schema(
            company_id=company_id,
            name="Usuario",
            slug="user",
            permissions=[
                "modules.view",
                "models.view",
            ],
            is_system=True
        )

        admin_role_id = MongoCollections.roles.insert_one(admin_role).inserted_id
        MongoCollections.roles.insert_one(manager_role)
        MongoCollections.roles.insert_one(user_role)

        return admin_role_id

    @staticmethod
    def assign_role_to_user(user_id: ObjectId, role_id: ObjectId) -> None:
        """
        Asigna un rol a un usuario.
        Premisa: un usuario pertenece a una sola empresa y tiene un solo rol.
        """

        MongoCollections.users.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "role_id": role_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
