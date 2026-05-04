from django.http import JsonResponse
from core.db.sqlite.models.modelo_prehecho import ModeloPrehecho


def listar_modelos_prehechos_view(request):
    # =========================
    # Usuario, empresa y relación usuario-empresa del contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        return JsonResponse({"error": "Contexto inválido"}, status=400)

    # =========================
    # Listar modelos prehechos activos
    # =========================
    modelos = ModeloPrehecho.objects.filter(activo=True)

    data = []
    for mod in modelos:
        data.append({
            "id": mod.id,
            "nombre": mod.nombre,
            "descripcion": mod.descripcion,
            "categoria": mod.categoria,
            "icono": mod.icono,
        })

    return JsonResponse({"modelos": data})