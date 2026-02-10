# core/db/sqlite/services/company_join_request_query_service.py

from core.db.sqlite.models.company_join_request import CompanyJoinRequest
from core.db.sqlite.models.user_company import UserCompany


class CompanyJoinRequestQueryService:
    """
    Consultas de solicitudes de unión pendientes.
    """

    @staticmethod
    def get_pending_for_owner(user):
        """
        Retorna solicitudes pendientes para las empresas
        donde el usuario es OWNER.
        """

        # =========================
        # Empresas donde es OWNER
        # =========================
        owner_companies = UserCompany.objects.filter(
            user=user,
            is_owner=True,
            is_active=True
        ).values_list("company_id", flat=True)

        if not owner_companies:
            return CompanyJoinRequest.objects.none()

        # =========================
        # Solicitudes pendientes
        # =========================
        return CompanyJoinRequest.objects.select_related(
            "user",
            "company",
            "invitation"
        ).filter(
            company_id__in=owner_companies,
            is_approved__isnull=True
        ).order_by("created_at")
