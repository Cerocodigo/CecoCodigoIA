# core/db/sqlite/services/join_company_service.py

from django.db import transaction
from django.core.exceptions import ValidationError

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany
from core.db.sqlite.models.company_invitation import CompanyInvitation

from core.db.sqlite.services.company_invitation_service import (
    CompanyInvitationService
)
from core.db.sqlite.services.company_join_request_service import (
    CompanyJoinRequestService
)


class JoinCompanyService:
    """
    Servicio para gestionar el ingreso de un usuario a una empresa
    mediante invitaciones (tokens).
    """

    # =========================
    # Join principal
    # =========================
    @staticmethod
    @transaction.atomic
    def join_company_by_token(
        *,
        user: User,
        token: str
    ) -> dict:
        """
        Intenta unir a un usuario a una empresa usando un token.

        Retorna un dict con el estado del proceso:
        - joined: bool
        - requires_approval: bool
        - company: Company
        """

        # =========================
        # Validar invitación
        # =========================
        invitation: CompanyInvitation = (
            CompanyInvitationService.validate_token(
                token=token,
                user_email=user.email
            )
        )

        company = invitation.company

        # =========================
        # Verificar si ya pertenece
        # =========================
        if UserCompany.objects.filter(
            user=user,
            company=company
        ).exists():
            raise ValidationError(
                "El usuario ya pertenece a esta empresa"
            )

        # =========================
        # Caso: requiere aprobación
        # =========================
        if invitation.requires_approval:
            CompanyJoinRequestService.create_request(
                user=user,
                company=company,
                invitation=invitation
            )

            return {
                "joined": False,
                "requires_approval": True,
                "company": company,
            }

        # =========================
        # Crear relación usuario-empresa
        # =========================
        UserCompany.objects.create(
            user=user,
            company=company,
            is_owner=False,
            is_active=True,
        )

        # =========================
        # Marcar invitación como usada
        # =========================
        if not invitation.is_general:
            invitation.is_used = True
            invitation.save(update_fields=["is_used"])

        return {
            "joined": True,
            "requires_approval": False,
            "company": company,
        }
