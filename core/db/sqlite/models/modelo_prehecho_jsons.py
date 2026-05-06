from django.db import models
from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho

class ModeloPrehechoJsons(models.Model):
    modelo = models.ForeignKey(
        ModeloPrehecho,
        on_delete=models.CASCADE,
        related_name="versiones"
    )
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(
        max_length=50,
        choices=[
            ("modulo", "Módulo"),
            ("modelo", "Modelo (DB)"),
            ("dashboard", "Dashboard"),
            ("plantillas_pdf", "Plantilla PDF"),
            ("reporte", "Reporte"),
        ]
    )
    # JSON completo restaurable
    json = models.JSONField()
    # opcional: prompt separado
    prompt_config = models.JSONField(blank=True, null=True)
    data_inicial = models.JSONField(blank=True, null=True, default=None)
    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.modelo.nombre} - {self.tipo}"