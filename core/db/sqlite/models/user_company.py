from django.db import models

from core.db.sqlite.models.user import User
from core.db.sqlite.models.company import Company


class UserCompany(models.Model):
    """
    Relación usuario - empresa.
    Permite múltiples empresas por usuario a futuro.
    """

    # =========================
    # Relaciones
    # =========================
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)

    # =========================
    # Rol estructural
    # =========================
    is_owner = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    role_slug = models.CharField(max_length=50,default="user")

    # =========================
    # Fechas
    # =========================
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_company"
        unique_together = ("user", "company")

    def __str__(self):
        return f"{self.user.email} → {self.company.razon_social}"
