# core/views/modules/module_new_reg_view.py
# =====================================
# Vista principal de un módulo - Nuevo registro
# =====================================


from django.shortcuts import render, redirect
from django.http import Http404
from django.http import JsonResponse
from django.urls import reverse

import json

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany

from core.db.mongo.services.modules.module_query_service import (ModuleQueryService,)
from core.db.mongo.services.models.model_query_service import (ModelQueryService,)

from core.db.mongo.services.dashboard.dashboard_query_service import (DashboardQueryService,)
from core.db.mongo.services.reports.report_query_service import (ReportQueryService,)
from core.db.mongo.services.pdf_templates.pdf_template_query_service import (PDFQueryService,)


from core.db.mysql.services.connection_service import (MySQLCompanyConnectionService,)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService

from core.services.modules.build_dynamic_form_service import (build_dynamic_form,)


from core.services.ai.modulos_openia_client import (AIService)


def module_edit_ia_main(request, module_id: str):

    # =========================
    # Contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        raise Http404("Contexto inválido")

    # =========================
    # Módulo
    # =========================
    module = ModuleQueryService.get_module_by_id(
        company=company,
        module_id=module_id,
    )

    if not module:
        raise Http404("Módulo no encontrado")

    # =========================
    # Modelos
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=module_id,
        is_raw=True,
    )

    modelo_cab = None
    modelos_det = []

    for model in models:
        if model["rol"] in ["maestro", "cabecera"]:
            modelo_cab = model
        elif model["rol"] == "detalle":
            modelos_det.append(model)

    if not modelo_cab:
        return render(request, "core/modules/module_main.html", {
            "error": "No existe entidad cabecera"
        })

    # =========================
    # 🔥 APLICAR CAMBIOS IA (SESSION)
    # =========================
    estructura_ia = request.session.get(f"estructura_ia_{module_id}")

    if estructura_ia:
        # Cabecera["campos"] 
        modelo_cab = estructura_ia.get("cabecera")

        # Detalles
        for det in modelos_det:
            for nuevo_det in estructura_ia.get("detalles", []):
                if str(det["_id"]) == str(nuevo_det["modelo_id"]):
                    det["campos"] = nuevo_det["campos"]

    # =========================
    # POST (guardar)
    # =========================
    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "guardar":

            FormCabecera = build_dynamic_form(
                modelo_cab["campos"], company, modelo_cab["_id"], False
            )

            form = FormCabecera(request.POST, request.FILES)

            if form.is_valid():
                # 🔹 tu lógica de guardado real aquí

                # 🔥 limpiar cambios IA
                request.session.pop(f"estructura_ia_{module_id}", None)

                return redirect(
                    reverse("core:module_edit_ia_main", args=[module_id])
                )

    # =========================
    # GET / RENDER
    # =========================
    FormCabecera = build_dynamic_form(
        modelo_cab["campos"], company, modelo_cab["_id"], False
    )

    FormsDetalle = []
    for det in modelos_det:
        FormsDetalle.append({
            "modelo_id": det["_id"],
            "entidad": det["tabla"],
            "display": det["display"],
            "form": build_dynamic_form(det["campos"], company, det["_id"], True)
        })

    return render(request, "core/modules/module_edit_ia.html", {
        "form": FormCabecera(),
        "formularios_detalle": [
            {
                "modelo_id": fDet["modelo_id"],
                "entidad": fDet["entidad"],
                "display": fDet["display"],
                "forms": [fDet["form"](prefix=f"{fDet['entidad']}_0")]
            } for fDet in FormsDetalle
        ],
        "titulo_topbar": module["nombre"] + (
            " - IA (preview)" if estructura_ia else ""
        ),
        "modo_ia": bool(estructura_ia),
        "module": module,
        "empresa": company,
        "moduloId": module['_id'],
    })
        

def module_edit_ia_requerimientos(request, module_id: str):

    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    # =========================
    # Contexto
    # =========================
    user = request.user_ctx
    company = request.company_ctx
    user_company = request.user_company_ctx

    if not user or not company or not user_company:
        return JsonResponse({"error": "Contexto inválido"}, status=400)

    # =========================
    # Módulo
    # =========================
    module = ModuleQueryService.get_active_modules(company)


    # =========================
    # Modelos
    # =========================
    models = ModelQueryService.get_models_actives_all(company=company)

    # =========================
    # INPUT
    # =========================
    modulo_actual = module_id
    prompt = request.POST.get("mensaje", "")  # 🔥 corregido
    previos = request.POST.get("previos", "")  # 🔥 corregido

    files = request.FILES.getlist("files")

    # 🔹 Procesar archivos (opcional pero potente)
    archivos_texto = []
    for f in files:
        try:
            contenido = f.read().decode("utf-8")
            archivos_texto.append(contenido)
        except:
            archivos_texto.append(f"[archivo binario: {f.name}]")


    # =========================
    # IA
    # estructura_nueva devuelve:
    #[Models]
    # =========================
    print('enviando a IA')
    try:
        respuestaAI = AIService.interpretar_prompt(
            prompt,previos,
            modulo_actual,
            module,
            models
            # 🔥 aquí luego puedes pasar archivos_texto si quieres
        )
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

    ## =========================Info
    #es cuando la ia esta pidiendo mas informacion o esta respondiendo a una accion que no es la generacion de modelos
    #por ejempl enviando un modelo de ejemplo o pidiendo aclaraciones
    if respuestaAI['respuesta'] == "info":
        return JsonResponse({
            "ok": True,
            "respuesta": respuestaAI['mensaje']
        })

    ## =========================Accion
    # creacion, modificacion eliminacion de json    
    if respuestaAI['respuesta'] == "accion":
        for accion in respuestaAI.get("acciones", []):
            if accion["fuente"] == "modulo":
                if accion["accion"] == "crear":
                    # Creación del módulo
                    module = ModuleQueryService.create_module(
                        company=company,
                        nombre=accion["data"]["nombre"],
                        descripcion=accion["data"]["descripcion"],
                        uso=accion["data"]["uso"],
                        entidades=accion["data"].get("entidades", [])
                    )

                if accion["accion"] == "modificar":
                    update_module = ModuleQueryService.update_module(
                        company=company,
                        module_id=accion["data"]["_id"],
                        nombre=accion["data"]["nombre"],
                        descripcion=accion["data"]["descripcion"],
                        uso=accion["data"]["uso"],
                        entidades=accion["data"].get("entidades", [])
                    )
                    
                if accion["accion"] == "eliminar":
                    delete_module = ModuleQueryService.delete_module(
                        company=company,
                        module_id=accion["data"]["_id"],
                    )

            if accion["fuente"] == "modelos":
                if accion["accion"] == "crear":
                    pass
                    
                if accion["accion"] == "modificar":
                    pass
                if accion["accion"] == "eliminar":
                    pass

            if accion["fuente"] == "campo":
                if accion["accion"] == "crear":
                    pass
                    
                if accion["accion"] == "modificar":
                    pass
                if accion["accion"] == "eliminar":
                    pass


            if accion["fuente"] == "reportes":
                if accion["accion"] == "crear":
                    pass
                if accion["accion"] == "modificar":
                    pass
                if accion["accion"] == "eliminar":
                    pass

            if accion["fuente"] == "pdf":
                if accion["accion"] == "crear":
                    pass
                if accion["accion"] == "modificar":
                    pass
                if accion["accion"] == "eliminar":
                    pass

            if accion["fuente"] == "dashboard":
                if accion["accion"] == "crear":
                    DashboardQueryService.create_dashboard(
                        company=company,
                        module_id=accion["data"]["module_id"],
                        nombre=accion["data"]["nombre"],
                    )
                    pass

                if accion["accion"] == "modificar":
                    DashboardQueryService.modifiar(
                        company=company,
                        module_id=accion["data"]["module_id"],
                        nombre=accion["data"]["nombre"],
                    )
                if accion["accion"] == "eliminar":
                    DashboardQueryService.delete_dashboard(
                        company=company,
                        module_id=accion["data"]["module_id"]
                    )
                    pass
            

        return JsonResponse({
            "ok": True,
            "respuesta": respuestaAI['mensaje']
        })
    




    # =========================
    # 🔥 GUARDAR EN SESSION
    # =========================
    modelo_cab = None
    modelos_det = []

    for model in respuestaAI['models']:
        if model["modulo"] == module_id:
            if model["rol"] in ["maestro", "cabecera"]:
                modelo_cab = model
            elif model["rol"] == "detalle":
                modelos_det.append(model)

    if modelo_cab == None:
        return JsonResponse({"error": "La IA no devolvió un modelo cabecera válido"}, status=500)
    
    request.session[f"estructura_ia_{module_id}"] = {'cabecera': modelo_cab, 'detalles': modelos_det}
    request.session.modified = True

    # =========================
    # RESPUESTA
    # =========================
    return JsonResponse({
        "ok": True,
        "respuesta": "Cambios generados correctamente",
        "estructura": request.session[f"estructura_ia_{module_id}"],
        "modelo_cab": modelo_cab,
        "modelos_det": modelos_det
    })