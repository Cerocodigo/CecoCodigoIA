# core/views/modules/module_main_view.py
# =====================================
# Vista principal de un módulo
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


def module_view_reg_view(request, module_id: str, id: int):
    print("module_view_reg_view called with module_id:", module_id, "and id:", id)
    """
    Vista principal del módulo:
    /module/<module_id>/view/
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
            try:
                with dml.transaction():
                    for det in modelos_det:
                        sql = f"DELETE FROM {det['tabla']} WHERE {det['fk']} = %s"
                        dml.delete(sql, (id,))
                        # cursor.execute(sql, (id,))

                    sql = f"DELETE FROM {tabla_cab} WHERE {pk} = %s"
                    dml.delete(sql, (id,))
                    # cursor.execute(sql, (id,))   

                    return redirect(
                        "modulo_form",
                        modulo=module["_id"]
                    )
            except Exception as e:
                return render(request, "modulos/consulta.html", {
                    "error": f"Error al eliminar: {str(e)}",
                    "titulo": module["nombre"],
                    "modulo": module
                })
                

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
            return render(request, "modulos/moduloNuevo.html", {
                "form": form_cab,
                "formularios_detalle": formularios_detalle,
                "titulo": module["nombre"],
                "modulo": module,
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
            # cursor.execute(sql, valores)

            # ---- DELETE + INSERT DETALLES ----
            for det in modelos_det:
                sql = f"DELETE FROM {det['tabla']} WHERE {det['fk']} = %s"
                dml.delete(sql, (id,))
                # cursor.execute(sql, (id,))

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
                # cursor.execute(sql, valores)

            # mysql.commit()

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
        return render(request, "modulos/consulta.html", {
            "error": "Registro no encontrado",
            "titulo": module["nombre"],
            "modulo": module
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
            forms.append(
                FormDet(initial=row, prefix=f"{det['tabla']}_{i}")
            )

        if not forms:
            forms.append(FormDet(prefix=f"{det['tabla']}_0"))

        formularios_detalle.append({
            "entidad": det["tabla"],
            "forms": forms
        })
    print("Get Preparado - Renderizando template")
    # return render(request, "modulos/moduloNuevo.html", {
    return render(request, "core/modules/module_new_reg.html", {
        "form": form_cab,
        "formularios_detalle": formularios_detalle,
        "titulo": module["nombre"],
        "moduloId": module["_id"],
        "modulo": module,
        "id": id,
        "user": user,
        "company": company,
        "user_role": user_company.role_slug if user_company else "user",
    })
