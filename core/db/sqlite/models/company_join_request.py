# core/db/sqlite/models/company_join_request.py

from django.db import models

from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company
from core.db.sqlite.models.company_invitation import CompanyInvitation


class CompanyJoinRequest(models.Model):
    """
    Solicitud de unión a una empresa que requiere aprobación.
    """

    # =========================
    # Relaciones
    # =========================
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    invitation = models.ForeignKey(
        CompanyInvitation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # =========================
    # Estado
    # =========================
    is_approved = models.BooleanField(null=True)  # None = pendiente
    decided_at = models.DateTimeField(null=True, blank=True)

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "company_join_requests"
        unique_together = ("user", "company")

    def __str__(self):
        return f"{self.user.email} → {self.company.razon_social} (pendiente)"
