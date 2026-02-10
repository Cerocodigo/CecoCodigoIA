from django.db import models


class MongoServer(models.Model):
    """
    Servidores MongoDB disponibles para empresas.
    Gestionados solo por el sistema.
    """

    # =========================
    # Identificación
    # =========================
    name = models.CharField(max_length=100)

    # =========================
    # Conexión
    # =========================
    uri = models.TextField()

    # =========================
    # Estado
    # =========================
    STATUS_CHOICES = (
        ("DISPONIBLE", "Disponible"),
        ("NO_DISPONIBLE", "No disponible"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="DISPONIBLE"
    )

    is_default = models.BooleanField(default=False)

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mongo_servers"

    def __str__(self):
        return f"{self.name} ({self.status})"
