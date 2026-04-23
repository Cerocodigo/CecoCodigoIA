from django.db import models
import uuid

from core.db.sqlite.models.company import Company


def generate_token():
    return uuid.uuid4().hex


class CompanyInvitation(models.Model):
    """
    Invitación para unirse a una empresa.
    Puede ser general o específica (por email),
    con o sin aprobación del OWNER.
    """

    # =========================
    # Relaciones
    # =========================
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="invitations"
    )

    # =========================
    # Token de invitación
    # =========================
    token = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        default=generate_token
    )

    # =========================
    # Tipo de invitación
    # =========================
    is_general = models.BooleanField(
        default=False,
        help_text="Invitación general reutilizable"
    )

    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Email destino si es invitación específica"
    )

    # =========================
    # Flujo de aprobación
    # =========================
    requires_approval = models.BooleanField(
        default=False,
        help_text="Si requiere aprobación del Dueño (OWNER)"
    )

    # =========================
    # Control de uso
    # =========================
    is_used = models.BooleanField(
        default=False,
        help_text="Marca si ya fue utilizada (solo para específicas)"
    )

    # =========================
    # Expiración
    # =========================
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha de expiración del token"
    )

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "company_invitations"

    # =========================
    # Lógica de dominio
    # =========================
    def is_expired(self) -> bool:
        from django.utils.timezone import now
        return self.expires_at is not None and self.expires_at < now()

    def __str__(self):
        return f"{self.company.nombre_comercial} | {self.token}"
