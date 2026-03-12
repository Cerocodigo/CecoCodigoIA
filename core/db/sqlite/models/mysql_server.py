from django.db import models


class MySQLServer(models.Model):
    """
    Servidores MySQL / MariaDB disponibles para empresas.
    """

    # =========================
    # Identificación
    # =========================
    name = models.CharField(max_length=100)

    # =========================
    # Conexión
    # =========================
    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField(default=3306)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=255)

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
        db_table = "mysql_servers"

    def __str__(self):
        return f"{self.name} ({self.status})"
