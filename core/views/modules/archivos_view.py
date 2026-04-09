import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from datetime import datetime


def subir_archivo(request):
    if request.method != "POST":
        return JsonResponse({"estado": False, "error": "Método no permitido"})

    archivo = request.FILES.get("archivo")
    campo = request.POST.get("campo")
    empresa = request.POST.get("empresa")

    if not archivo:
        return JsonResponse({"estado": False, "error": "No se recibió archivo"})

    if not empresa:
        return JsonResponse({"estado": False, "error": "Empresa requerida"})

    try:
        # =========================
        # 1️⃣ RUTA BASE
        # =========================
        fecha = datetime.now().strftime("%Y/%m/%d")

        carpeta = os.path.join(
            settings.MEDIA_ROOT,
            "companies",
            str(empresa)
        )

        os.makedirs(carpeta, exist_ok=True)

        # =========================
        # 2️⃣ NOMBRE ÚNICO
        # =========================
        nombre_original = archivo.name
        extension = nombre_original.split(".")[-1]

        nombre_archivo = f"{datetime.now().strftime('%H%M%S%f')}.{extension}"

        ruta_completa = os.path.join(carpeta, nombre_original)

        # =========================
        # 3️⃣ GUARDAR ARCHIVO
        # =========================
        with open(ruta_completa, "wb+") as destino:
            for chunk in archivo.chunks():
                destino.write(chunk)

        # =========================
        # 4️⃣ RUTA RELATIVA
        # =========================
        ruta_relativa = os.path.join(
            "companies",
            str(empresa),
            nombre_original
        ).replace("\\", "/")

        url = settings.MEDIA_URL + ruta_relativa

        # =========================
        # 5️⃣ RESPUESTA
        # =========================
        return JsonResponse({
            "estado": True,
            "ruta": ruta_relativa,  # 🔥 esto guardas en DB
            "url": url              # 🔥 esto usas para preview
        })

    except Exception as e:
        return JsonResponse({
            "estado": False,
            "error": str(e)
        })