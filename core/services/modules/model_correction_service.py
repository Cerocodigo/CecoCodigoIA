# core/services/modules/model_correction_service.py

import copy
import unicodedata
import re

from core.services.modules.constants import (
    CECOD_CONFIG_META,
    MODEL_DEFAULTS,
    FIELD_DEFAULTS,
    FIELD_REQUIRED_FIELDS,
    MODEL_REQUIRED_FIELDS,
    TIPO_FUNCIONAL_META,
    AREAS_ROL,
)

from core.services.modules.model_validator_service import ModelValidatorService


class ModelCorrectionService:
    """
    Servicio encargado de aplicar correcciones automáticas a un modelo. 
    Correcciones incluyen:
        - Completar campos faltantes con valores por defecto
        - Eliminar campos no permitidos
        - Inferir campos a partir de otros (ej: _id, display)
        - Corregir inconsistencias (ej: tipo_base vs tipo_funcional)
    El objetivo es que el modelo resultante esté lo más cerca posible de ser válido,
    aunque no se garantiza que sea 100% correcto. Siempre se recomienda revisar los cambios aplicados.

    Flujo:
        correct()
            ├── Corregir metadata general
            └── Corregir campos
    """

    # ==================================================
    # ENTRYPOINT PRINCIPAL
    # ==================================================
    @classmethod
    def correct(cls, model: dict):
        """Aplica correcciones automáticas a un modelo dinámico.
        Correcciones aplicadas directamente sobre una copia del modelo original.
        """
        data = copy.deepcopy(model)
        changes = []

        cls._correct_metadata(data, changes)
        cls._correct_fields(data, changes)

        return {
            "corrected_model": data,
            "changes": changes,
        }

    # ==================================================
    # CORRECCIÓN DE METADATA
    # ==================================================
    @classmethod
    def _correct_metadata(cls, data, changes):
        """Aplica correcciones a nivel de metadata general del modelo."""
        # -------------------------
        # 1. ELIMINAR CAMPOS NO PERMITIDOS
        # -------------------------
        required = set(MODEL_REQUIRED_FIELDS["base"])

        if data.get("rol") == "detalle":
            required |= MODEL_REQUIRED_FIELDS["detalle_extra"]

        for key in list(data.keys()):
            if key not in required:
                del data[key]
                changes.append(f"metadata.{key} eliminado")

        # -------------------------
        # 2. AGREGAR FALTANTES
        # -------------------------
        for key, default in MODEL_DEFAULTS.items():
            if key not in data:
                data[key] = default
                changes.append(f"metadata.{key} agregado")

        # -------------------------
        # 3. INFERENCIAS
        # -------------------------
        if not data.get("_id") and data.get("tabla"):
            data["_id"] = cls._slugify(data["tabla"])
            changes.append("_id inferido")

        if not data.get("tabla") and data.get("_id"):
            data["tabla"] = data["_id"]
            changes.append("tabla inferida")

        if not data.get("display") and data.get("_id"):
            data["display"] = cls._humanize(data["_id"])
            changes.append("display generado")

        if not data.get("modulo") and data.get("_id"):
            data["modulo"] = data["_id"]
            changes.append("modulo inferido")

    # ==================================================
    # CORRECCIÓN DE CAMPOS
    # ==================================================
    @classmethod
    def _correct_fields(cls, data, changes):
        """Aplica correcciones a nivel de campos dentro del modelo."""
        campos = data.get("campos", [])
        rol = data.get("rol")
        config_area = AREAS_ROL.get(rol, AREAS_ROL["cabecera"])

        for i, campo in enumerate(campos):
            path = f"campos[{i}]"

            # -------------------------
            # 1. ELIMINAR CAMPOS NO PERMITIDOS
            # -------------------------
            for key in list(campo.keys()):
                if key not in FIELD_REQUIRED_FIELDS:
                    del campo[key]
                    changes.append(f"{path}.{key} eliminado")

            # -------------------------
            # 2. AGREGAR DEFAULTS BASE
            # -------------------------
            for key, default in FIELD_DEFAULTS.items():
                if key not in campo:
                    campo[key] = default
                    changes.append(f"{path}.{key} agregado")

            # -------------------------
            # 3. GENERAR ETIQUETA
            # -------------------------
            if not campo.get("etiqueta") and campo.get("nombre"):
                campo["etiqueta"] = cls._humanize(campo["nombre"])
                changes.append(f"{path}.etiqueta generada")

            tipo_funcional = campo.get("tipo_funcional")
            tipo_base = campo.get("tipo_base")

            # -------------------------
            # 4. CORREGIR tipo_base SEGÚN tipo_funcional
            # -------------------------
            meta = TIPO_FUNCIONAL_META.get(tipo_funcional)
            if meta and tipo_base not in meta["bases_validas"]:
                campo["tipo_base"] = meta["base_default"]
                changes.append(f"{path}.tipo_base corregido")

            # -------------------------
            # 5. NORMALIZAR valor_default
            # -------------------------
            result = ModelValidatorService.normalize_and_validate(
                campo.get("valor_default"),
                campo.get("tipo_base")
            )

            if result["was_changed"]:
                campo["valor_default"] = result["value"]
                changes.append(f"{path}.valor_default corregido")

            # -------------------------
            # 6. CORREGIR CONFIGURACIÓN
            # -------------------------
            cls._correct_config(campo, path, changes)

            # -------------------------
            # 7. VALIDAR O ASIGNAR AREA SEGÚN ROL
            # -------------------------
            if "area" not in campo or campo.get("area") not in config_area["areas_validas"]:
                campo["area"] = config_area["area_default"]
                changes.append(f"{path}.area corregido a default")

        # -------------------------
        # 8. REORDENAMIENTO
        # -------------------------
        cls._fix_orders(campos, changes)

    # ==================================================
    # CORRECCIÓN DE CONFIGURACIÓN
    # ==================================================
    @classmethod
    def _correct_config(cls, campo, path, changes):
        """Aplica correcciones a nivel de configuración de un campo."""
        config = campo.get("configuracion")

        # Asegurar dict
        if not isinstance(config, dict):
            campo["configuracion"] = {}
            config = campo["configuracion"]
            changes.append(f"{path}.configuracion reiniciada")

        tipo = campo.get("tipo_funcional")
        meta = CECOD_CONFIG_META.get(tipo)

        if not meta:
            return

        expected = meta["structure"]
        defaults = meta["defaults"]

        # -------------------------
        # 1. ELIMINAR EXTRAS
        # -------------------------
        for key in list(config.keys()):
            if key not in expected:
                del config[key]
                changes.append(f"{path}.configuracion.{key} eliminado")

        # -------------------------
        # 2. AGREGAR FALTANTES (si aplica)
        # -------------------------
        if defaults is None:
            return

        for key in expected:
            if key not in config:
                config[key] = defaults.get(key)
                changes.append(f"{path}.configuracion.{key} agregado")

    # ==================================================
    # REORDENAMIENTO NORMAL (POR ÁREA)
    # ==================================================
    @staticmethod
    def _fix_orders(campos, changes):
        """
        Aplica correcciones de ordenamiento a los campos del modelo.
        El ordenamiento se hace primero por área (main, lateral, etc) y luego por orden dentro de cada área.
        Campos sin orden se colocan al final.
        """

        areas = {}
        for idx, campo in enumerate(campos):
            area = campo.get("area")
            areas.setdefault(area, []).append((idx, campo))

        for area, items in areas.items():

            items_sorted = sorted(
                items,
                key=lambda x: (
                    x[1].get("orden") if isinstance(x[1].get("orden"), int) else 9999,
                    x[0]
                )
            )

            for new_order, (idx, campo) in enumerate(items_sorted, start=1):
                old = campo.get("orden")
                if old != new_order:
                    campo["orden"] = new_order
                    changes.append(f"campos[{idx}].orden {old}->{new_order}")


    # ==================================================
    # UTILIDADES
    # ==================================================
    @staticmethod
    def _slugify(text):
        """Convierte un texto a formato slug para usar como _id o tabla."""
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[ \-]+", "_", text.lower())
        text = re.sub(r"[^a-z0-9_]", "", text)
        return re.sub(r"_+", "_", text).strip("_")

    @staticmethod
    def _humanize(text):
        """Convierte un texto tipo slug a formato humanizado para usar como display o etiqueta."""
        return text.replace("_", " ").title()