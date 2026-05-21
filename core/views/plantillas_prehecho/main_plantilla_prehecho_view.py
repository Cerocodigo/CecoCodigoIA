# core/views/plantillas_prehecho/aplicar_plantilla_prehecho_view.py
# =====================================
# Vista Aplicar plantilla prehecho
# =====================================

from django.shortcuts import render
from django.http import Http404

from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho


def main_plantilla_prehecho_view(request, plantilla_id):
    """
    Vista para iniciar el flujo de aplicación
    de plantilla prehecha.
    """

    # =========================
    # Contexto empresa/usuario
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")

    # =========================
    # Obtener plantilla
    # =========================
    try:
        plantilla = ModeloPrehecho.objects.get(
            id=plantilla_id,
            activo=True,
        )

    except ModeloPrehecho.DoesNotExist:
        raise Http404("Plantilla no encontrada")

    # =========================
    # Obtener metadata ejecutable
    # =========================
    ejecuciones = plantilla.ejecuciones.filter(
        activo=True
    ).order_by("id")

    # =========================
    # Context
    # =========================
    context = {
        "plantilla": plantilla,
        "ejecuciones": ejecuciones,
    }

    return render(
        request,
        "core/plantillas_prehecho/aplicar_plantilla_prehecho.html",
        context,
    )