from django.db import models
from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho

class ModeloPrehechoEjecutar(models.Model):
    modelo = models.ForeignKey(
        ModeloPrehecho,
        on_delete=models.CASCADE,
        related_name="ejecuciones"
    )
    descripcion = models.TextField(blank=True)

    # Ejecutar MongoDB
    data_variables_mongo = models.JSONField(blank=True, null=True, default=None)
    
    # Ejecutables Mysql
    data_inicial_mysql = models.JSONField(blank=True, null=True, default=None)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.modelo.nombre} - Ejecución"