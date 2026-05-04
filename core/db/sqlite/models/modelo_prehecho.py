from django.db import models

class ModeloPrehecho(models.Model):
    nombre = models.CharField(max_length=150)
    descripcion = models.TextField(blank=True)

    categoria = models.CharField(max_length=100, blank=True)
    activo = models.BooleanField(default=True)

    icono = models.CharField(max_length=50, blank=True)  # emoji o icono o url de img

    created_at = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre