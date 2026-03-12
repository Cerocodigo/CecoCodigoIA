# core/db/sqlite/services/company_invitation_service.py

from datetime import timedelta
from django.utils.timezone import now
from django.core.exceptions import ValidationError

from core.db.sqlite.models.company_invitation import CompanyInvitation
from core.db.sqlite.models.company import Company


class CompanyInvitationService:
    """
    Servicio para creación y validación de invitaciones de empresa.
    """

    # =========================
    # Creación de invitaciones
    # =========================
    @staticmethod
    def create_invitation(
        company: Company,
        *,
        is_general: bool,
        email: str | None = None,
        requires_approval: bool = False,
        expires_hours: int | None = None
    ) -> CompanyInvitation:
        """
        Crea una invitación general o específica.
        """

        if not is_general and not email:
            raise ValidationError("Una invitación específica requiere un email")

        expires_at = None
        if expires_hours:
            expires_at = now() + timedelta(hours=expires_hours)

        invitation = CompanyInvitation.objects.create(
            company=company,
            is_general=is_general,
            email=email if not is_general else None,
            requires_approval=requires_approval,
            expires_at=expires_at,
        )

        return invitation

    # =========================
    # Validación de token
    # =========================
    @staticmethod
    def validate_token(token: str, user_email: str) -> CompanyInvitation:
        """
        Valida un token de invitación y retorna la invitación válida.
        """

        try:
            invitation = CompanyInvitation.objects.select_related("company").get(
                token=token
            )
        except CompanyInvitation.DoesNotExist:
            raise ValidationError("Invitación inválida")

        # =========================
        # Expiración
        # =========================
        if invitation.is_expired():
            raise ValidationError("La invitación ha expirado")

        # =========================
        # Validación específica
        # =========================
        if not invitation.is_general:
            if invitation.is_used:
                raise ValidationError("La invitación ya fue utilizada")

            if invitation.email.lower() != user_email.lower():
                raise ValidationError("Esta invitación no es para tu correo")

        return invitation

