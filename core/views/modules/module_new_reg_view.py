# core/views/modules/module_new_reg_view.py
# =====================================
# Vista principal de un módulo - Nuevo registro
# =====================================


from django.shortcuts import render, redirect
from django.http import Http404
from django.http import JsonResponse
import json

from core.db.sqlite.models.user import User
from core.db.sqlite.models.user_company import UserCompany

from core.db.mongo.services.modules.module_query_service import (ModuleQueryService,)
from core.db.mongo.services.models.model_query_service import (ModelQueryService,)

from core.db.mysql.services.connection_service import (MySQLCompanyConnectionService,)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService

from core.services.modules.build_dynamic_form_service import (build_dynamic_form,)


def module_new_reg_view(request, module_id: str):
    """
    Vista principal del módulo:
    /module/<module_id>/new/
    """

    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")
    
    # =========================
    # Relación usuario-empresa
    # =========================
    user_company = UserCompany.objects.filter(
        user=user,
        company=request.company_ctx,
        is_active=True
    ).first()

    
    # =========================
    # Obtener módulo (Mongo)
    # =========================
    module = ModuleQueryService.get_module_by_id(
        company=company,
        module_id=module_id,
    )

    if not module:
        raise Http404("Módulo no encontrado")

    # =========================
    # Obtener modelos del módulo (Mongo)
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=module_id,
        is_raw=True,
    )

    modelo_cab = None
    modelos_det = []

    for model in models:
        entidad = model["tabla"]
        rol = model["rol"]

        if rol == "cabecera":
            modelo_cab = model
        elif rol == "detalle":
            modelos_det.append(model)

    if not modelo_cab:
        return render(request, "core/modules/module_main.html", {
            "error": "No existe entidad cabecera"
        })
    

    #* Post

    #* Get
    if request.method == "GET":
        FormCabecera = build_dynamic_form(modelo_cab["campos"], company, modelo_cab["_id"])

        FormsDetalle = []
        for i, det in enumerate(modelos_det):
            campos = det["campos"]
            FormsDetalle.append({
                "modelo_id": det["_id"],
                "entidad": det["tabla"],
                "display": det["display"],
                "form": build_dynamic_form(campos, company, det["_id"])
            })


        return render(request, "core/modules/module_new_reg.html", {
            "form": FormCabecera(),
            "formularios_detalle": [
                {
                    "modelo_id": fDet["modelo_id"],
                    "entidad": fDet["entidad"],
                    "display": fDet["display"],
                    "forms": [fDet["form"]()]
                } for fDet in FormsDetalle
            ],
            "titulo_topbar": module["nombre"] + " - Nuevo registro",
            "module": module,
            "success": "estructura actualizada correctamente",    
            "empresa": company,
            "moduloId": module['_id'],
            "user": user,
            "company": company,
            "user_role": user_company.role_slug if user_company else "user",
            })
        
    
 
def calculosReferenciaBuscador(request, modelo, campo):
    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")

    # =========================
    # Obtener modelos del módulo (Mongo)
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=modelo,
        is_raw=True,
    )

    if not models:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # 2️⃣ Buscar campo
    campo_conf = next(
        (c for c in models[0].get("campos", []) if c.get("nombre") == campo),
        None
    )

    if not campo_conf:
        return JsonResponse({"estado": False, "msg": "campo no existe en el modelo"})

    # 3️⃣ Verificar tipo funcional
    if campo_conf.get("tipo_funcional") != "ReferenciaBuscador":
        return JsonResponse({
            "estado": True,
            "msg": "campo no es ReferenciaBuscador",
            "valor": None
        })

    config = campo_conf.get("configuracion", {})

    sql_template = config.get("sql")
    if len(request.body) >0:
        variables_valores =  json.loads(request.body.decode("utf-8"))
        variables_conf =  config.get("parametros")
    else:
        variables_valores= []
        variables_conf =  None

    if not sql_template:
        return JsonResponse({
            "estado": False,
            "msg": "SQL no definido en configuración"
        })

    # 4️⃣ Resolver variables
    sql = sql_template

    if variables_conf:
        # formato soportado: "@Var@=CampoFormulario"
        pares = variables_conf.split(",")
        for par in pares:
            var_sql, campo_origen = par.split("=")
            valor = variables_valores[campo_origen]
            if valor is None:
                return JsonResponse({
                    "estado": False,
                    "msg": f"valor no enviado para {campo_origen}"
                })

            sql = sql.replace(var_sql, str(valor))
            

    q = request.GET.get("q")
    qq = ' and ('
    
    Campos_filtros = config.get("campos_filtrables")
    if len(q)>0:
        for campo in Campos_filtros:
            qq = qq + '' + campo+ ' like "%' + q + '%" or ' 
        qq = qq[:-3] + ')'
        sql = sql + qq

    # 5️⃣ Ejecutar SQL
    try:
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            rows = dml.fetch_all(sql, params=None)
        finally:
            try:
                connection.close()
            except Exception:
                pass

        return JsonResponse({
            "estado": True,
            "resultados": rows,
            "Campos_filtros":Campos_filtros
        })

    except Exception as e:
        return JsonResponse({
            "estado": False,
            "msg": "Error ejecutando SQL",
            "error": str(e)
        })




def calculosNumeroSecuencial(request, modelo, campo):
    # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")

    # =========================
    # Obtener modelos del módulo (Mongo)
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=modelo,
        is_raw=True,
    )

    if not models:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # 2️⃣ Buscar campo
    campo_conf = next(
        (c for c in models[0].get("campos", []) if c.get("nombre") == campo),
        None
    )

    if not campo_conf:
        return JsonResponse({"estado": False, "msg": "campo no existe en el modelo"})

    # 3️⃣ Verificar tipo funcional
    if campo_conf.get("tipo_funcional") != "NumeroSecuencial":
        return JsonResponse({
            "estado": True,
            "msg": "campo no es secuencial",
            "valor": None
        })

    campo = campo_conf.get("nombre")
    tabla = models.get("tabla")
    sql = f"""
        SELECT COALESCE(MAX({campo}), 0) AS actual
        FROM {tabla}
    """

    # 5️⃣ Ejecutar SQL
    try:
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)
        try:
            rows = dml.fetch_all(sql, params=None)
            actual = rows[0]["actual"] if rows and rows["actual"] is not None else 0
            siguiente = actual + 1
            return JsonResponse({
                "estado": True,
                "tipo": "NumeroSecuencial",
                "campo": campo,
                "tabla": tabla,
                "actual": actual,
                "siguiente": siguiente
            })
        finally:
            try:
                connection.close()
            except Exception:
                pass
    except Exception as e:
        return JsonResponse({
            "estado": False,
            "msg": "Error ejecutando SQL",
            "error": str(e)
        })



def calculosQueryBaseDatos(request, modelo, campo):
       # =========================
    # Usuario autenticado
    # =========================
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("accounts:login")

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return redirect("accounts:login")

    company = getattr(request, "company_ctx", None)
    if not company:
        raise Http404("Empresa no disponible en el contexto")

    # =========================
    # Obtener modelos del módulo (Mongo)
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=modelo,
        is_raw=True,
    )

    if not models:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # 2️⃣ Buscar campo
    campo_conf = next(
        (c for c in models[0].get("campos", []) if c.get("nombre") == campo),
        None
    )

    if not campo_conf:
        return JsonResponse({"estado": False, "msg": "campo no existe en el modelo"})

    # 3️⃣ Verificar tipo funcional
    if campo_conf.get("tipo_funcional") != "QueryBaseDatos":
        return JsonResponse({
            "estado": True,
            "msg": "campo no es QueryBaseDatos",
            "valor": None
        })

    config = campo_conf.get("configuracion", {})
    sql_template = config.get("query")['sql']
    variables_valores =  json.loads(request.body.decode("utf-8"))
    variables_conf =  config.get("parametros")

    if not sql_template:
        return JsonResponse({
            "estado": False,
            "msg": "SQL no definido en configuración"
        })

    # 4️⃣ Resolver variables
    sql = sql_template

    if variables_conf:
        # formato soportado: "@Var@=CampoFormulario"
        pares = variables_conf.split(",")
        for par in pares:
            print('par >>>', par)
            var_sql, campo_origen = par.split("=")
            valor = variables_valores[campo_origen]
            print("valor >>>", valor)
            if valor is None:
                return JsonResponse({
                    "estado": False,
                    "msg": f"valor no enviado para {campo_origen}"
                })

            sql = sql.replace(var_sql, str(valor))

        try:
            connection = MySQLCompanyConnectionService.get_connection_for_company(
                company=company
            )
            executor = MySQLExecutor(connection)
            dml = MySQLDMLService(executor)

            try:
                rows = dml.fetch_all(sql, params=None)
                valor = list(rows.values())[0] if rows else None

            finally:
                try:
                    connection.close()
                except Exception:
                    pass
            return JsonResponse({
                "estado": True,
                "tipo": "QueryBaseDatos",
                "campo": campo,
                "valor": valor
            })

        except Exception as e:
            return JsonResponse({
                "estado": False,
                "msg": "Error ejecutando SQL",
                "error": str(e)
            })


