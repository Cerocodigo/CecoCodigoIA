# core/db/sqlite/services/company_join_request_service.py

from django.utils.timezone import now
from django.core.exceptions import ValidationError
from django.db import transaction

from core.db.sqlite.models.company_join_request import CompanyJoinRequest
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company
from core.db.sqlite.models.company_invitation import CompanyInvitation


class CompanyJoinRequestService:
    """
    Servicio para gestionar solicitudes de unión a empresas
    que requieren aprobación del OWNER.
    """

    # =========================
    # Crear solicitud
    # =========================
    @staticmethod
    @transaction.atomic
    def create_request(
        *,
        user: User,
        company: Company,
        invitation: CompanyInvitation
    ) -> CompanyJoinRequest:
        """
        Crea una solicitud de unión pendiente de aprobación.
        """

        if not invitation.requires_approval:
            raise ValidationError(
                "La invitación no requiere aprobación"
            )

        if CompanyJoinRequest.objects.filter(
            user=user,
            company=company
        ).exists():
            raise ValidationError(
                "Ya existe una solicitud pendiente para esta empresa"
            )

        return CompanyJoinRequest.objects.create(
            user=user,
            company=company,
            invitation=invitation,
            is_approved=None
        )

    # =========================
    # Listar pendientes del OWNER
    # =========================
    @staticmethod
    def list_pending_for_owner(owner_user: User):
        """
        Retorna todas las solicitudes pendientes
        de las empresas donde el usuario es OWNER.
        """

        # Empresas donde el usuario es OWNER
        owner_companies = UserCompany.objects.filter(
            user=owner_user,
            is_owner=True
        ).values_list("company_id", flat=True)

        if not owner_companies:
            return CompanyJoinRequest.objects.none()

        return (
            CompanyJoinRequest.objects
            .select_related(
                "user",
                "company",
                "invitation"
            )
            .filter(
                company_id__in=owner_companies,
                is_approved__isnull=True
            )
            .order_by("created_at")
        )

    # =========================
    # Aprobar solicitud
    # =========================
    @staticmethod
    @transaction.atomic
    def approve(request_id: int, owner_user: User) -> None:
        """
        Aprueba una solicitud y une al usuario a la empresa.
        """

        try:
            join_request = CompanyJoinRequest.objects.select_related(
                "company", "user", "invitation"
            ).get(id=request_id)
        except CompanyJoinRequest.DoesNotExist:
            raise ValidationError("Solicitud no encontrada")

        if join_request.is_approved is not None:
            raise ValidationError("La solicitud ya fue procesada")

        if not UserCompany.objects.filter(
            user=owner_user,
            company=join_request.company,
            is_owner=True
        ).exists():
            raise ValidationError(
                "No tienes permisos para aprobar esta solicitud"
            )

        UserCompany.objects.create(
            user=join_request.user,
            company=join_request.company,
            is_owner=False,
            is_active=True
        )

        if join_request.invitation and not join_request.invitation.is_general:
            join_request.invitation.is_used = True
            join_request.invitation.save(update_fields=["is_used"])

        join_request.is_approved = True
        join_request.decided_at = now()
        join_request.save(
            update_fields=["is_approved", "decided_at"]
        )

    # =========================
    # Rechazar solicitud
    # =========================
    @staticmethod
    def reject(request_id: int, owner_user: User) -> None:
        """
        Rechaza una solicitud pendiente.
        """

        try:
            join_request = CompanyJoinRequest.objects.select_related(
                "company"
            ).get(id=request_id)
        except CompanyJoinRequest.DoesNotExist:
            raise ValidationError("Solicitud no encontrada")

        if join_request.is_approved is not None:
            raise ValidationError("La solicitud ya fue procesada")

        if not UserCompany.objects.filter(
            user=owner_user,
            company=join_request.company,
            is_owner=True
        ).exists():
            raise ValidationError(
                "No tienes permisos para rechazar esta solicitud"
            )

        join_request.is_approved = False
        join_request.decided_at = now()
        join_request.save(
            update_fields=["is_approved", "decided_at"]
        )
