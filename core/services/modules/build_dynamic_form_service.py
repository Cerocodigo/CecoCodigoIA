from django import forms
from django.forms import widgets, Select

from core.db.mysql.services.connection_service import (
    MySQLCompanyConnectionService,
)
from core.db.mysql.executor import MySQLExecutor
from core.db.mysql.services.dml_service import MySQLDMLService


BASE_FIELD_TYPES = {
    "string": forms.CharField,
    "char": forms.CharField,
    "decimal": forms.DecimalField,
    "decimal2": forms.DecimalField,
    "decimal4": forms.DecimalField,
    "decimal6": forms.DecimalField,
    "int": forms.IntegerField,
    "email": forms.EmailField,
    "boolean": forms.BooleanField,
    "date": forms.DateField,
    "datetime": forms.DateTimeField,
    "fecha": forms.DateField,
}

UI_FIELD_TYPES = {
    "image": forms.ImageField,
    "file": forms.FileField,
}

FK_FIELD_TYPES = {
    "fk": forms.ModelChoiceField
}

# 🔒 Tipos no editables globales
NO_EDITABLE_CECOD_TYPES = {
    "NumeroSecuencial",
    "SistemaFecha",
    "SistemaUsuario",
    "ReferenciaAdjunto",
    "QueryBaseDatos",
    "Operacion",
    "FormatoTexto",
    "Condicional",
    "FormulaDetalle",
    "LlaveExterna"
}

def build_dynamic_form(campos, company, modelo, es_detalle=False):
    #def build_dynamic_form(campos, company, modelo):
    form_fields = {}
    campos = sorted(campos, key=lambda c: c.get("orden", 1000))

    for campo in campos:
        nombre = campo.get("nombre")
        etiqueta = campo.get("etiqueta", nombre)
        tipo_base = campo.get("tipo_base")
        tipo_funcional = campo.get("tipo_funcional")
        requerido = campo.get("requerido", False)
        configuracion = campo.get("configuracion", {})

        # layout metadata
        visible = campo.get("visible", True)
        col = campo.get("col", 3)
        gap = campo.get("gap", 0)
        gap_top = campo.get("gap_top", 0)
        break_line = campo.get("break", False)
        area = campo.get("area", "Main-Arriba")

        # attrs base
        widget_attrs = {
            "id": f"id_{nombre}",
            "class": "form-control",
            "data_col": col,
            "data_gap": gap,
            "data_gap_top": gap_top,
            "data_break": break_line,
            "data_area": area,
            "visible": visible,
            "data_tipo": tipo_funcional,
            "data-modelo": modelo,
            "data-name": nombre,
            
            
            
        }
        if es_detalle:
            widget_attrs["data-name"] = nombre  # opcional (para JS)
            widget_attrs.pop("id", None)  # ❌ evitar IDs repetidos
        else:
            widget_attrs["id"] = f"id_{nombre}"

        # 🔒 regla global
        if tipo_funcional in NO_EDITABLE_CECOD_TYPES:
            widget_attrs["readonly"] = "readonly"


        if tipo_base == "int":
            widget_attrs["data-decimales"] = 0
        if tipo_base == "decimal":
            widget_attrs["data-decimales"] = 2
        if tipo_base == "decimal2":
            widget_attrs["data-decimales"] = 2

        if tipo_base == "decimal4":
            widget_attrs["data-decimales"] = 4

        if tipo_base == "decimal6":
            widget_attrs["data-decimales"] = 6

        # ====================================================
        # 🔽 OPCIÓN MÚLTIPLE
        # ====================================================
        if tipo_funcional == "OpcionMultiple":
            opciones = configuracion.get("opciones", [])
            labels = configuracion.get("labels", {})
            choices = [(op, labels.get(op, op)) for op in opciones]
            
            widget_attrs.update({
                "class": "form-select form-control-erp",
                "style": "width: 100%",
            })


            form_fields[nombre] = forms.ChoiceField(
                label=etiqueta,
                choices=choices,
                required=requerido,
                initial=configuracion.get("valor_predeterminado"),
                widget=forms.Select(attrs=widget_attrs)  # ✅ FIX
            )

            continue

        # ====================================================
        # 🔽 REFERENCIA BUSCADOR
        # ====================================================
        if tipo_funcional == "ReferenciaBuscador":
            tipo_base = "string"

            widget_attrs["data-label_field"] = configuracion.get("label_field")
            widget_attrs["data-value_field"] = configuracion.get("value_field")

            if "parametros" in configuracion:
                parametros = configuracion["parametros"].split(",")
                widget_attrs["data-variables"] = ",".join(
                    [p.split("=")[1] for p in parametros]
                )
            else:
                widget_attrs["data-variables"] = ""

            widget_attrs["data-valorinicial"] = configuracion.get("valor_inicial", "")
            widget_attrs["data_ModuloIngresoRapido"] = configuracion.get("ModuloIngresoRapido", "")
            

        # ====================================================
        # 🔽 REFERENCIA
        # ====================================================
        if tipo_funcional == "Referencia":
            choices, extra_data = obtener_opciones_sql(company, configuracion)

            widget_attrs.update({
                "class": "form-select form-control-erp",
                "style": "width: 100%",
                "data-ref-source": nombre,
            })

            form_fields[nombre] = forms.ChoiceField(
                label=etiqueta,
                required=requerido,
                choices=choices,
                widget=SelectWithData(attrs=widget_attrs, extra_data=extra_data)
            )
            continue

        # ====================================================
        # 📎 REFERENCIA ADJUNTO (CORREGIDO)
        # ====================================================
        if tipo_funcional == "ReferenciaAdjunto":

            ref = configuracion.get("referencia")
            campo_origen = configuracion.get("campo_origen")

            if configuracion.get("editable") == "No":
                widget_attrs["readonly"] = "readonly"

            widget_attrs.update({
                "data-ref-from": f"{ref}",
                "data-ref-key": campo_origen,
            })

            field_class = BASE_FIELD_TYPES.get(tipo_base, forms.CharField)

            kwargs = {
                "label": etiqueta,
                "required": False,
                "widget": field_class.widget(attrs=widget_attrs)
            }

            if tipo_base == "decimal":
                kwargs["decimal_places"] = 2
                kwargs["max_digits"] = 18

            if tipo_base == "decimal4":
                kwargs["decimal_places"] = 4
                kwargs["max_digits"] = 18
                
            if tipo_base == "decimal6":
                kwargs["decimal_places"] = 6
                kwargs["max_digits"] = 18


            if tipo_base == "string":
                kwargs["max_length"] = 255

            form_fields[nombre] = field_class(**kwargs)
            continue

        # ====================================================
        # 🔽 CONFIGURACIONES ESPECIALES
        # ====================================================
        if tipo_funcional == "NumeroSimple":
            widget_attrs["data-min"] = configuracion.get("min")
            

        if tipo_funcional == "FormulaDetalle":
            
            widget_attrs["data-operacion"] = configuracion.get("operacion")
            widget_attrs["data-campo"] = configuracion.get("campo")
            widget_attrs["data-tabla"] = configuracion.get("tabla")
            widget_attrs["data-condicion"] = configuracion.get("condicion")

        if tipo_funcional == "TextoSimple":
            if configuracion.get("editable") == "No":
                widget_attrs["readonly"] = "readonly"

            widget_attrs["data-unico"] = configuracion.get("unico")
            widget_attrs["data-valor_predeterminado"] = configuracion.get("valor_predeterminado")
            

        if tipo_funcional == "FechaRegistro":
            if configuracion.get("editable") == "No":
                widget_attrs["readonly"] = "readonly"

        if tipo_funcional == "Archivo":
            widget_attrs.update({
                "class": "form-control form-control-erp",
                "data_acepta": configuracion.get("acepta_archivo", "cualquiera"),
                "data_maxsize": configuracion.get("tamano_max_mb", 10),
                "data_tipo": tipo_funcional,
            })

            # form_fields[nombre] = forms.FileField(
            #     label=etiqueta,
            #     required=requerido,
            #     widget=forms.ClearableFileInput(attrs=widget_attrs)
            # )
            # continue

        if tipo_funcional == "Operacion":
            widget_attrs["data-formula"] = configuracion.get("formula")

        if tipo_funcional == "Condicional":
            widget_attrs["data-condiciones"] = configuracion.get("condicional", [])
            widget_attrs["data-si_no"] = configuracion.get("si_no", "")

        if tipo_funcional == "FormatoTexto":
            widget_attrs["data-template"] = configuracion.get("template")
            widget_attrs["data-padding"] = configuracion.get("padding")

        if tipo_funcional == "QueryBaseDatos":
            if "parametros" in configuracion:
                parametros = configuracion["parametros"].split(",")
                widget_attrs["data-variables"] = ",".join(
                    [p.split("=")[1] for p in parametros]
                )
            else:
                widget_attrs["data-variables"] = ""

        # ====================================================
        # 🔽 CAMPOS NORMALES
        # ====================================================
        field_class = BASE_FIELD_TYPES.get(tipo_base)
        if not field_class:
            continue

        kwargs = {
            "label": etiqueta,
            "required": requerido,
            "widget": field_class.widget(attrs=widget_attrs)
        }

        if tipo_base == "decimal":
            kwargs["decimal_places"] = 2
            kwargs["max_digits"] = 18


        if tipo_base == "decimal2":
            kwargs["decimal_places"] = 2
            kwargs["max_digits"] = 18

        if tipo_base == "decimal4":
            kwargs["decimal_places"] = 4
            kwargs["max_digits"] = 18

        if tipo_base == "decimal6":
            kwargs["decimal_places"] = 6
            kwargs["max_digits"] = 18

        if tipo_base == "date":
            kwargs["widget"] = widgets.DateInput(
                attrs={**widget_attrs, "type": "date"}
            )

        if tipo_base == "datetime":
            kwargs["widget"] = widgets.DateTimeInput(
                attrs={**widget_attrs, "type": "datetime-local"}
            )

        if tipo_base == "string":
            kwargs["max_length"] = 255

        form_fields[nombre] = field_class(**kwargs)

    return type("DynamicForm", (forms.Form,), form_fields)


# ====================================================
# 🔽 SQL HELPERS
# ====================================================

def obtener_opciones_sql(company, campo):
    sql = campo.get("sql")
    value_field = campo.get("value_field")
    label_field = campo.get("label_field")

    connection = MySQLCompanyConnectionService.get_connection_for_company(company=company)
    executor = MySQLExecutor(connection)
    dml = MySQLDMLService(executor)

    try:
        rows = dml.fetch_all(sql, params=None)
    finally:
        try:
            connection.close()
        except Exception:
            pass

    choices = []
    data_map = {}

    for row in rows:
        value = row[value_field]
        label = row[label_field]

        choices.append((value, label))

        extra = {label_field: label}
        for k, v in row.items():
            if k not in (value_field, label_field):
                extra[k] = v

        data_map[value] = extra

    return choices, data_map


class SelectWithData(Select):
    def __init__(self, *args, extra_data=None, **kwargs):
        self.extra_data = extra_data or {}
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(
            name, value, label, selected, index, subindex=subindex, attrs=attrs
        )

        if value in self.extra_data:
            for k, v in self.extra_data[value].items():
                option["attrs"][f"data-{k.lower()}"] = v

        return option