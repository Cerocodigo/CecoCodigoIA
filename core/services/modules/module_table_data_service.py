# core/services/modules/module_table_data_service.py
# ==================================================
# Servicio de obtención y transformación de datos
# para la tabla principal de un módulo
# ==================================================

from datetime import date, datetime

from core.db.mysql.services.module_data_query_service import (
    ModuleDataQueryService,
)


class ModuleTableDataService:
    """
    Servicio responsable de:

    - Obtener datos desde MySQL
    - Aplicar transformaciones estructurales
    - Preparar columnas y filas para la UI
    """

    # ==================================================
    # Serialización básica
    # ==================================================

    @staticmethod
    def serialize_value(value):
        """
        Serializa valores especiales para evitar
        formateo automático de Django en templates.

        - datetime -> "dd/mm/YYYY HH:MM"
        - date     -> "dd/mm/YYYY"
        - otros    -> se retornan igual
        """

        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y %H:%M")

        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")

        return value

    # ==================================================
    # Metadata de campos (Mongo)
    # ==================================================

    @staticmethod
    def build_field_metadata(model_definition: dict) -> dict:
        """
        Construye metadata simplificada de campos
        para uso en UI y transformaciones.

        Considera:
        - Solo incluir campos con visible=True
        - Siempre incluir id_* aunque visible=False

        Retorna:
        {
            nombre: {
                "etiqueta": str,
                "tipo_funcional": str,
                "configuracion": {}
            }
        }
        """

        metadata = {}
        pk_isVisible = False
        campo_pk = model_definition.get("pk", "")

        for campo in model_definition.get("campos", []):

            nombre = campo.get("nombre")
            etiqueta = campo.get("etiqueta", nombre)
            tipo_funcional = campo.get("tipo_funcional")
            visible = campo.get("visible", True)

            es_pk = (nombre == campo_pk)
            if not visible and not es_pk:
                continue
            if es_pk and visible:
                pk_isVisible = True

            configuracion = {}

            if tipo_funcional == "OpcionMultiple":
                config_original = campo.get("configuracion", {}) or {}

                opciones = config_original.get("opciones", [])
                labels = config_original.get("labels")

                # Si no hay labels, generarlos automáticamente
                if not labels:
                    labels = {str(op): str(op) for op in opciones}
                else:
                    # Asegurar que claves y valores sean string
                    labels = {str(k): str(v) for k, v in labels.items()}

                configuracion = {
                    "opciones": opciones,
                    "labels": labels,
                }

            metadata[nombre] = {
                "etiqueta": etiqueta,
                "tipo_funcional": tipo_funcional,
                "configuracion": configuracion,
            }

        return metadata, pk_isVisible


    # ==================================================
    # Obtención principal de tabla
    # ==================================================

    @staticmethod
    def get_table_data(company, model_definition: dict, limit: int = 1000):
        """
        Retorna columnas, filas y metadata procesadas para la tabla principal.

        CAMBIO IMPORTANTE:
        - columns ya NO es lista de strings
        - ahora es lista de objetos:
            [
                {"nombre": "...", "etiqueta": "..."},
                ...
            ]

        - Oculta columna PK (id_*)
        - Separa pk del resto de valores
        - Serializa fechas
        - Traduce OpcionMultiple usando labels
        """

        try:
            # =========================
            # Metadata desde Mongo 
            # =========================
            field_metadata, pk_isVisible = ModuleTableDataService.build_field_metadata(
                model_definition
            )

            # =========================
            # Fetch desde MySQL
            # =========================
            raw_columns, rows = ModuleDataQueryService.fetch_table_data(
                company=company,
                table_name=model_definition["tabla"],
                campos=model_definition["campos"],
                limit=limit,
            )

            # =========================
            # Construcción columnas estructuradas
            # =========================
            structured_columns = []
            filtered_column_names = []
            pk_index = None
            campo_pk = model_definition.get("pk", "")

            for index, col in enumerate(raw_columns):
                if col == campo_pk:
                    pk_index = index
                    if not pk_isVisible:
                        continue

                metadata = field_metadata.get(col, {})

                structured_columns.append({
                    "nombre": col,
                    "etiqueta": metadata.get("etiqueta", col),
                })

                filtered_column_names.append(col)

            # =========================
            # Procesamiento de filas
            # =========================
            filtered_rows = []

            for row in rows:
                row = list(row)
                pk_value = row[pk_index] if pk_index is not None else None

                transformed_values = []
                for index, value in enumerate(row):
                    if index == pk_index and not pk_isVisible:
                        continue

                    column_name = raw_columns[index]
                    metadata = field_metadata.get(column_name, {})

                    # Serialización base
                    value = ModuleTableDataService.serialize_value(value)

                    # Traducción OpcionMultiple
                    if metadata.get("tipo_funcional") == "OpcionMultiple":
                        labels = metadata.get("configuracion", {}).get("labels", {})
                        value = labels.get(str(value), value)

                    transformed_values.append(value)
                
                filtered_rows.append({
                    "pk": pk_value,
                    "values": transformed_values,
                })

            return structured_columns, filtered_rows, field_metadata

        except Exception as e:
            return [], [], {}
