from django.db import models

from core.db.sqlite.models.mongo_server import MongoServer
from core.db.sqlite.models.mysql_server import MySQLServer

from django_countries import countries


class Company(models.Model):
    """
    Empresa registrada en el sistema.
    """

    # =========================
    # Datos generales
    # =========================
    nombre_comercial = models.CharField(max_length=255)
    pais = models.CharField(
        max_length=2,
        choices=list(countries),
        default='EC'
    )

    # =========================
    # Conexiones MongoDB
    # =========================
    mongo_server = models.ForeignKey(
        MongoServer,
        on_delete=models.PROTECT
    )
    mongo_db_name = models.CharField(max_length=100)

    # =========================
    # Conexiones MySQL
    # =========================
    mysql_server = models.ForeignKey(
        MySQLServer,
        on_delete=models.PROTECT
    )
    mysql_db_name = models.CharField(max_length=100, default="")
    mysql_db_user = models.CharField(max_length=100, default="")
    mysql_db_password = models.CharField(max_length=255, default="")

    # =========================
    # Url logo de la empresa
    # =========================
    logo_url = models.URLField(max_length=500, blank=True, null=True, default="")

    # =========================
    # Estado
    # =========================
    is_active = models.BooleanField(default=True)

    # =========================
    # Fechas
    # =========================
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "companies"

    def __str__(self):
        return self.nombre_comercial
