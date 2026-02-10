# core/mongo/schemas/role.py

from datetime import datetime
from bson import ObjectId


def role_schema(
    company_id: ObjectId,
    name: str,
    slug: str,
    permissions: list[str],
    is_system: bool = False
) -> dict:
    """
    Esquema base de un rol por empresa
    """

    return {
        "_id": ObjectId(),
        "company_id": company_id,
        "name": name,
        "slug": slug,
        "permissions": permissions,
        "is_system": is_system,
        "is_active": True,
        "created_at": datetime.utcnow(),
    }
