# core/views/modules/module_view_reg_view.py
# =====================================
# Vista principal de un módulo - Visualizar registro
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

from core.services.modules.delete_module_record_service import DeleteModuleRecordService

from core.services.ui.message_service import set_view_msg, pop_view_msg


def module_view_reg_view(request, module_id: str, id: int):
    """
    Vista principal del módulo:
    /module/<module_id>/view/<id>/
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
    # Modo de la vista (VIEW / EDIT)
    # =========================
    url_name = request.resolver_match.url_name

    is_view = url_name == "module_view_reg_view"
    is_edit = url_name == "module_edit_reg_view"

    
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
    # Obtener modelos del módulo (Mongo) por rol (cabecera-detalle)
    # =========================
   

    Modelo = ModelQueryService.get_models_for_module_rol(
        company=company,
        module_id=module_id,
        module_rol="cabecera"
    )[0]

    modelos_det = ModelQueryService.get_models_for_module_rol(
        company=company,
        module_id=module_id,
        module_rol="detalle"
    )

    tabla_cab = Modelo["tabla"]
    pk = Modelo["pk"]
    campos_cab = [c for c in Modelo["campos"] if c.get("activo", True)]
    cab_id = Modelo["_id"]

    # Bloquear edición en modo solo lectura
    if request.method == "POST" and is_view:
        raise Http404("No permitido en modo vista")

    # =====================================================
    # ======================= POST =======================
    # =====================================================
    if request.method == "POST":
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        accion = request.POST.get("accion")

        # ---------- DELETE ----------
        if accion == "eliminar":

            success, error = DeleteModuleRecordService.execute(
                company=company,
                module_id=module_id,
                record_id=id
            )

            if success:
                set_view_msg(request, "success", "Registro eliminado correctamente")
                return redirect("core:module_main", module_id=module_id)
            else:
                set_view_msg(request, "danger", f"Error al eliminar: {error}")
                return redirect("core:module_view_reg_view", module_id=module_id, id=id)

                

        # ---------- UPDATE ----------
        FormCab = build_dynamic_form(campos_cab, company, cab_id)
        form_cab = FormCab(request.POST)

        forms_detalle = []
        for det in modelos_det:
            FormDet = build_dynamic_form(det["campos"], company, det["_id"])
            i = 0
            while f"{det['tabla']}_{i}-" in "".join(request.POST.keys()):
                forms_detalle.append({
                    "modelo": det,
                    "form": FormDet(
                        request.POST,
                        prefix=f"{det['tabla']}_{i}"
                    )
                })
                i += 1

        if not form_cab.is_valid() or any(not f["form"].is_valid() for f in forms_detalle):
            return render(request, "modulos/module_new_reg.html", {
                "form": form_cab,
                "formularios_detalle": formularios_detalle,
                "titulo_topbar": module["nombre"] + (" - Consultar" if is_view else " - Editar"),
                "module": module,
                "id": id,
                "error": "Corrige los errores del formulario"
            })

        # ---- UPDATE CABECERA ----
        sets = []
        valores = []

        for campo in campos_cab:
            nombre = campo["nombre"]
            if campo.get("editable", True):
                sets.append(f"{nombre} = %s")
                valores.append(form_cab.cleaned_data.get(nombre))

        valores.append(id)

        with dml.transaction():
            sql = f"""
                UPDATE {tabla_cab}
                SET {', '.join(sets)}
                WHERE {pk} = %s
            """
            dml.update(sql, valores)

            # ---- DELETE + INSERT DETALLES ----
            for det in modelos_det:
                sql = f"DELETE FROM {det['tabla']} WHERE {det['fk']} = %s"
                dml.delete(sql, (id,))

            for f in forms_detalle:
                modelo_det = f["modelo"]
                fk = modelo_det["fk"]

                campos = []
                valores = []

                for k, v in f["form"].cleaned_data.items():
                    campos.append(k)
                    valores.append(v)

                campos.append(fk)
                valores.append(id)

                sql = f"""
                    INSERT INTO {modelo_det['tabla']}
                    ({','.join(campos)})
                    VALUES ({','.join(['%s'] * len(valores))})
                """
                dml.insert(sql, valores)

            return redirect(
                "modulo_form",
                modulo=module["_id"],
                id=id
            )

    # =====================================================
    # ======================= GET ========================
    # =====================================================

    sql = f"SELECT * FROM {tabla_cab} WHERE {pk} = %s"
    connection = MySQLCompanyConnectionService.get_connection_for_company(
        company=company
    )
    executor = MySQLExecutor(connection)
    dml = MySQLDMLService(executor)

    try:
        registro = dml.fetch_one(sql, params=(id,))
    finally:
        try:
            connection.close()
        except Exception:
            pass

    if not registro:
        return render(request, "core/modules/module_new_reg.html", {
            "error": "Registro no encontrado",
            "titulo_topbar": module["nombre"] + (" - Consultar" if is_view else " - Editar"),
            "modulo": module,
            "id": id,
        })

    FormCab = build_dynamic_form(campos_cab, company, cab_id)

    initial_cab = {}
    for campo in campos_cab:
        nombre = campo["nombre"]
        if nombre in registro:
            valor = registro[nombre]
            if campo.get("tipo_funcional") == "boolean":
                valor = bool(valor)
            initial_cab[nombre] = valor

    form_cab = FormCab(initial=initial_cab)

    if is_view:
        for field in form_cab.fields.values():
            field.disabled = True

    formularios_detalle = []

    for det in modelos_det:
        sql = f"SELECT * FROM {det['tabla']} WHERE {det['fk']} = %s"
        connection = MySQLCompanyConnectionService.get_connection_for_company(
            company=company
        )
        executor = MySQLExecutor(connection)
        dml = MySQLDMLService(executor)

        try:
            rows = dml.fetch_all(sql, params=(id,))
        finally:
            try:
                connection.close()
            except Exception:
                pass
        
        FormDet = build_dynamic_form(det["campos"], company, det['_id'])
        forms = []

        for i, row in enumerate(rows):
            form_instance = FormDet(initial=row, prefix=f"{det['tabla']}_{i}")

            if is_view:
                for field in form_instance.fields.values():
                    field.disabled = True

            forms.append(form_instance)

        if not forms:
            form_instance = FormDet(prefix=f"{det['tabla']}_0")

            if is_view:
                for field in form_instance.fields.values():
                    field.disabled = True

            forms.append(form_instance)

        formularios_detalle.append({
            "modelo_id": det["_id"],
            "entidad": det["tabla"],
            "display": det["display"],
            "forms": forms
        })


    # =========================
    # Obtener mensaje flash
    # =========================
    view_msg = pop_view_msg(request)

    return render(request, "core/modules/module_new_reg.html", {
        "form": form_cab,
        "formularios_detalle": formularios_detalle,
        "titulo_topbar": module["nombre"] + (" - Consultar" if is_view else " - Editar"),
        "moduloId": module["_id"],
        "module": module,
        "id": id,
        "user": user,
        "company": company,
        "user_role": user_company.role_slug if user_company else "user",
        "view_msg": view_msg,
        "is_view": is_view,
        "is_edit": is_edit,
    })


def module_delete_reg_view(request, module_id: str, id: int):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"success": False, "error": "No autenticado"}, status=401)

    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        request.session.flush()
        return JsonResponse({"success": False, "error": "Sesión inválida"}, status=401)

    company = getattr(request, "company_ctx", None)
    if not company:
        return JsonResponse({"success": False, "error": "Empresa no disponible"}, status=400)

    success, error = DeleteModuleRecordService.execute(
        company=company,
        module_id=module_id,
        record_id=id
    )

    if success:
        return JsonResponse({
            "success": True,
            "message": "Registro eliminado correctamente"
        })
    else:
        return JsonResponse({
            "success": False,
            "error": error or "Error desconocido"
        })