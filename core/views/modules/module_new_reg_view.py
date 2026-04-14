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
        company=company,
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
    # Obtener modelos
    # =========================
    models = ModelQueryService.get_models_for_module(
        company=company,
        module_id=module_id,
        is_raw=True,
    )

    modelo_cab = None
    modelos_det = []

    for model in models:
        if model["rol"] == "maestro":
            modelo_cab = model
        if model["rol"] == "cabecera":
            modelo_cab = model
        elif model["rol"] == "detalle":
            modelos_det.append(model)

    if not modelo_cab:
        return render(request, "core/modules/module_main.html", {
            "error": "No existe entidad cabecera"
        })

    # =========================
    # POST (guardar)
    # =========================
    if request.method == "POST":

        # === CABECERA ===
        FormCabecera = build_dynamic_form(
            modelo_cab["campos"], company, modelo_cab["_id"], 
        )
        
        form_cab = FormCabecera(request.POST, request.FILES)
        # === DETALLES ===
        forms_detalle = []
        for det in modelos_det:
            FormDet = build_dynamic_form(det["campos"], company, det["_id"])
            form_det = FormDet(request.POST, prefix=str(det["_id"]))
            forms_detalle.append({
                "modelo": det,
                "form": form_det
            })

        # =========================
        # VALIDACIÓN
        # =========================
        valid_detalles = (
            all(f["form"].is_valid() for f in forms_detalle)
            if forms_detalle else True
        )

        if form_cab.is_valid() and valid_detalles:

            try:
                cab_id = guardar_con_transaccion(
                    company,
                    modelo_cab,
                    form_cab,
                    modelos_det,
                    forms_detalle
                )

                url = reverse(
                    "core:module_view_reg_view",
                    kwargs={
                        "module_id": module_id,
                        "id": cab_id
                    }
                )

                return redirect(url)

            except Exception as e:
                return render(request, "core/modules/module_new_reg.html", {
                    "form": form_cab,
                    "formularios_detalle": [
                        {
                            "modelo_id": f["modelo"]["_id"],
                            "entidad": f["modelo"]["tabla"],
                            "display": f["modelo"]["display"],
                            "forms": [f["form"]]
                        } for f in forms_detalle
                    ],
                    "error": str(e),
                    "titulo_topbar": module["nombre"] + " - Nuevo registro",
                    "module": module,
                    "empresa": company,
                    "moduloId": module['_id'],
                    "user": user,
                    "company": company,
                    "user_role": user_company.role_slug if user_company else "user",
                })

        else:
            # ❌ Validación fallida
            return render(request, "core/modules/module_new_reg.html", {
                "form": form_cab,
                "formularios_detalle": [
                    {
                        "modelo_id": f["modelo"]["_id"],
                        "entidad": f["modelo"]["tabla"],
                        "display": f["modelo"]["display"],
                        "forms": [f["form"]]
                    } for f in forms_detalle
                ],
                "titulo_topbar": module["nombre"] + " - Nuevo registro",
                "module": module,
                "empresa": company,
                "moduloId": module['_id'],
                "user": user,
                "company": company,
                "user_role": user_company.role_slug if user_company else "user",
            })

    # =========================
    # GET (formulario vacío)
    # =========================
    FormCabecera = build_dynamic_form(
        modelo_cab["campos"], company, modelo_cab["_id"]
    )

    FormsDetalle = []
    for det in modelos_det:
        FormsDetalle.append({
            "modelo_id": det["_id"],
            "entidad": det["tabla"],
            "display": det["display"],
            "form": build_dynamic_form(det["campos"], company, det["_id"])
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
        "empresa": company,
        "moduloId": module['_id'],
        "user": user,
        "company": company,
        "user_role": user_company.role_slug if user_company else "user",
    })
    
 
def calculosReferenciaBuscador(request, modelo, campo, fila=None):

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
    # Obtener modelos (Mongo)
    # =========================
    model = ModelQueryService.get_model_by_id(
        company=company,
        model_id=modelo,
        is_raw=True,
    )

    if not model:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # =========================
    # Buscar campo
    # =========================
    campo_conf = next(
        (c for c in model.get("campos", []) if c.get("nombre") == campo),
        None
    )

    if not campo_conf:
        return JsonResponse({"estado": False, "msg": "campo no existe en el modelo"})

    if campo_conf.get("tipo_funcional") != "ReferenciaBuscador":
        return JsonResponse({
            "estado": True,
            "msg": "campo no es ReferenciaBuscador",
            "valor": None
        })

    config = campo_conf.get("configuracion", {})
    sql_template = config.get("sql")

    if not sql_template:
        return JsonResponse({
            "estado": False,
            "msg": "SQL no definido en configuración"
        })

    # =========================
    # Inicializar SQL y params
    # =========================
    sql = sql_template
    params = []

    # =========================
    # Variables dinámicas (SEGURAS)
    # =========================
    if len(request.body) > 0:
        variables_valores = json.loads(request.body.decode("utf-8"))
        variables_conf = config.get("parametros")
    else:
        variables_valores = {}
        variables_conf = None

    if variables_conf:
        pares = variables_conf.split(",")

        for par in pares:
            var_sql, campo_origen = par.split("=")
            valor = variables_valores.get(campo_origen)

            if valor is None:
                return JsonResponse({
                    "estado": False,
                    "msg": f"valor no enviado para {campo_origen}"
                })

            # 🔥 reemplazo seguro
            sql = sql.replace(var_sql, "%s")
            params.append(valor)

    # =========================
    # Filtro buscador (LIKE seguro)
    # =========================
    q = request.GET.get("q", "").strip()
    Campos_filtros = config.get("campos_filtrables", [])

    if q and Campos_filtros:
        like_value = f"%{q}%"
        filtros = []

        for campo_filtro in Campos_filtros:
            filtros.append(f"{campo_filtro} LIKE %s")
            params.append(like_value)

        sql_lower = sql.lower()

        if " where " in sql_lower:
            sql += f" AND ({' OR '.join(filtros)})"
        else:
            sql += f" WHERE ({' OR '.join(filtros)})"

    # =========================
    # Ejecutar SQL
    # =========================
    try:
        connection = MySQLCompanyConnectionService.get_connection_for_company( company=company )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            rows = dml.fetch_all(sql, tuple(params))
        finally:
            try:
                connection.close()
            except Exception:
                pass

        return JsonResponse({
            "estado": True,
            "resultados": rows,
            "Campos_filtros": Campos_filtros,
            "Campo": campo_conf.get("nombre", ''),
            "fila": fila,
        })

    except Exception as e:
        return JsonResponse({
            "estado": False,
            "msg": "Error ejecutando SQL",
            "error": str(e),
            "sql_debug": sql,
            "params_debug": params
        })

def calculosNumeroSecuencial(request, modelo, campo, fila=None):
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
    model = ModelQueryService.get_model_by_id(
        company=company,
        model_id=modelo,
        is_raw=True,
    )

    if not model:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # 2️⃣ Buscar campo
    campo_conf = next(
        (c for c in model.get("campos", []) if c.get("nombre") == campo),
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
    tabla = model.get("tabla")
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
                "siguiente": siguiente,
                "fila":fila
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


import json
from django.http import JsonResponse, Http404
from django.shortcuts import redirect

def calculosQueryBaseDatos(request, modelo, campo, fila=None):

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
    # Obtener modelo
    # =========================
    model = ModelQueryService.get_model_by_id(
        company=company,
        model_id=modelo,
        is_raw=True,
    )

    if not model:
        return JsonResponse({"estado": False, "msg": "modelo no encontrado"})

    # =========================
    # Buscar campo
    # =========================
    campo_conf = next(
        (c for c in model.get("campos", []) if c.get("nombre") == campo),
        None
    )

    if not campo_conf:
        return JsonResponse({"estado": False, "msg": "campo no existe en el modelo"})

    if campo_conf.get("tipo_funcional") != "QueryBaseDatos":
        return JsonResponse({
            "estado": True,
            "msg": "campo no es QueryBaseDatos",
            "valor": None
        })

    config = campo_conf.get("configuracion", {})
    sql_template = config.get("query", {}).get("sql")
    variables_conf = config.get("parametros")

    if not sql_template:
        return JsonResponse({
            "estado": False,
            "msg": "SQL no definido en configuración"
        })

    # =========================
    # Leer valores del request
    # =========================
    try:
        variables_valores = json.loads(request.body.decode("utf-8"))
    except:
        return JsonResponse({
            "estado": False,
            "msg": "JSON inválido"
        })

    # =========================
    # Construir parámetros seguros
    # =========================
    params = {}
    sql = sql_template

    if variables_conf:
        pares = variables_conf.split(",")

        for par in pares:
            var_sql, campo_origen = par.split("=")

            if campo_origen not in variables_valores:
                return JsonResponse({
                    "estado": False,
                    "msg": f"Falta valor para {campo_origen}"
                })

            params[var_sql.replace("@", "")] = variables_valores[campo_origen]

        # Reemplazar @Var por %(Var)s
        for key in params.keys():
            sql = sql.replace(f"@{key}@", f"%({key})s")

    # =========================
    # Ejecutar SQL
    # =========================
    try:
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            rows = dml.fetch_all(sql, params=params)

            if not rows:
                valor = None
            elif len(rows) == 1 and len(rows[0]) == 1:
                valor = list(rows[0].values())[0]
            else:
                valor = rows  # devuelve todo si es complejo

        finally:
            connection.close()

        return JsonResponse({
            "estado": True,
            "tipo": "QueryBaseDatos",
            "campo": campo,
            "valor": valor,
            "fila":fila
        })

    except Exception as e:
        return JsonResponse({
            "estado": False,
            "msg": "Error ejecutando SQL",
            "error": str(e)
        })




def guardar_con_transaccion(company, modelo_cab, form_cab, modelos_detalle, forms_detalle):
    connection = MySQLCompanyConnectionService.get_connection_for_company(
        company=company
    )

    try:
        # 🔥 IMPORTANTE: desactivar autocommit
        try:
            connection.autocommit(False)
        except:
            connection.autocommit = False

        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        # 🔥 INICIAR TRANSACCIÓN
        connection.begin()

        # =========================
        # INSERT CABECERA
        # =========================
        data_cab = {
            k: v for k, v in form_cab.cleaned_data.items()
            if v is not None and v != ""
        }

        if not data_cab:
            raise Exception("No hay datos para la cabecera")

        columns = ", ".join(data_cab.keys())
        placeholders = ", ".join(["%s"] * len(data_cab))
        values = tuple(data_cab.values())

        sql_cab = f"INSERT INTO {modelo_cab['tabla']} ({columns}) VALUES ({placeholders})"

        # 🔥 INSERT devuelve ID directamente
        cab_id = dml.insertDevUltimo(sql_cab, values)

        # =========================
        # INSERT DETALLES
        # =========================
        for det in forms_detalle:
            form_det = det["form"]
            modelo_det = det["modelo"]

            if not form_det.cleaned_data:
                continue

            data_det = {
                k: v for k, v in form_det.cleaned_data.items()
                if v is not None and v != ""
            }

            # Inyectar FK automáticamente
            fk_name = modelo_det.get("fk")
            if fk_name:
                data_det[fk_name] = cab_id

            if not data_det:
                continue

            columns = ", ".join(data_det.keys())
            placeholders = ", ".join(["%s"] * len(data_det))
            values = tuple(data_det.values())

            sql_det = f"INSERT INTO {modelo_det['tabla']} ({columns}) VALUES ({placeholders})"

            dml.insert(sql_det, values)

        # ✅ TODO OK → COMMIT
        connection.commit()

        return cab_id

    except Exception as e:
        # ❌ ERROR → ROLLBACK REAL
        try:
            connection.rollback()
        except Exception as rollback_error:
            print("Error en rollback:", rollback_error)

        raise e

    finally:
        connection.close()