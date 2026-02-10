from bson import ObjectId
from core.mongo.collections import MongoCollections


def build_request_context(request):
    """
    Construye el contexto global del request
    (usuario + empresa activa)
    """

    user_id = request.session.get("user_id")
    company_id = request.session.get("company_id")

    if not user_id or not company_id:
        return None

    # Usuario (mínimo)
    user = MongoCollections.users.find_one(
        {"_id": ObjectId(user_id)},
        {"password": 0}  # nunca exponer password
    )

    # Empresa activa
    company = MongoCollections.companies.find_one(
        {"_id": ObjectId(company_id)}
    )

    if not user or not company:
        return None

    return {
        "user": {
            "id": str(user["_id"]),
            "email": user.get("email"),
            "name": f'{user.get("first_name", "")} {user.get("last_name", "")}'.strip()
        },
        "company": {
            "id": str(company["_id"]),
            "name": company.get("name"),
            "ruc": company.get("ruc")
        }
    }
