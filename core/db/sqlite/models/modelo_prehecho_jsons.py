from django.db import models
from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho

class ModeloPrehechoJsons(models.Model):
    modelo = models.ForeignKey(
        ModeloPrehecho,
        on_delete=models.CASCADE,
        related_name="jsons"
    )
    descripcion = models.TextField(blank=True)
    # El tipo debe coincidir con el nombre de la colección en MongoDB para facilitar la restauración
    tipo = models.CharField(
        max_length=50,
        choices=[
            ("modulos", "Módulo"),
            ("modelos", "Modelo (DB)"),
            ("dashboard", "Dashboard"),
            ("plantillas_pdf", "Plantilla PDF"),
            ("reportes", "Reporte"),
        ]
    )
    # JSON completo restaurable
    json = models.JSONField()
    # opcional: prompt separado
    prompt_config = models.JSONField(blank=True, null=True)

    activo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.modelo.nombre} - {self.tipo}"