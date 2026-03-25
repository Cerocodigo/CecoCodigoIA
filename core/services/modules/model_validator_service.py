# core/services/modules/model_validator_service.py

import json
import re

from core.services.modules.constants import (
    SQL_TYPES_KEYS,
    CECOD_TYPES,
    CECOD_CONFIG_STRUCTURE,
)


class ModelValidatorService:

    # =========================
    # ENTRYPOINT
    # =========================

    @classmethod
    def validate(cls, model_json):
        errors = []

        data = cls._validate_json(model_json, errors)
        if data is None:
            return cls._build_response(errors)

        cls._validate_metadata_structure(data, errors)
        cls._validate_metadata_semantics(data, errors)

        campos = data.get("campos", [])
        cls._validate_fields_structure(campos, errors)
        cls._validate_fields_semantics(data, campos, errors)
        cls._validate_field_configurations(campos, errors)

        return cls._build_response(errors)

    # =========================
    # RESPONSE
    # =========================

    @staticmethod
    def _build_response(errors):
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    # =========================
    # JSON VALIDATION
    # =========================

    @staticmethod
    def _validate_json(model_json, errors):
        if isinstance(model_json, dict):
            return model_json

        try:
            return json.loads(model_json)
        except Exception:
            errors.append({
                "tipoError": "JSON inválido",
                "ubicacion": "modelo completo",
                "elemento": "JSON inválido",
                "sugerenciaCorreccion": "Asegúrate de que el modelo sea un JSON válido"
            })
            return None

    # =========================
    # METADATA STRUCTURE
    # =========================

    @classmethod
    def _validate_metadata_structure(cls, data, errors):

        required = {
            "_id",
            "activo",
            "tabla",
            "display",
            "rol",
            "pk",
            "campos",
            "modulo",
        }

        if data.get("rol") == "detalle":
            required.add("fk")

        cls._validate_exact_keys(data, required, "", errors)

    # =========================
    # METADATA SEMANTICS
    # =========================

    @classmethod
    def _validate_metadata_semantics(cls, data, errors):

        # slug validation
        for key in ["_id", "tabla"]:
            val = data.get(key)
            if val and not re.match(r"^[a-z0-9_]+$", val):
                errors.append({
                    "tipoError": "Slug inválido",
                    "ubicacion": key,
                    "elemento": val,
                    "sugerenciaCorreccion": "Debe ser slug válido (minúsculas, números y _)"
                })

        campos = data.get("campos", [])
        nombres = [c.get("nombre") for c in campos]

        # PK obligatorio
        if data.get("pk") not in nombres:
            errors.append({
                "tipoError": "PK inválido",
                "ubicacion": "pk",
                "elemento": data.get("pk"),
                "sugerenciaCorreccion": "El pk definido en el modelo debe existir en los campos"
            })

        # FK obligatorio en detalle
        if data.get("rol") == "detalle":
            if data.get("fk") not in nombres:
                errors.append({
                    "tipoError": "FK inválido",
                    "ubicacion": "fk",
                    "elemento": data.get("fk"),
                    "sugerenciaCorreccion": "El fk definido en el modelo detalle debe existir en los campos"
                })

    # =========================
    # FIELDS STRUCTURE
    # =========================

    @classmethod
    def _validate_fields_structure(cls, campos, errors):

        required = {
            "visible",
            "nombre",
            "etiqueta",
            "tipo_base",
            "tipo_funcional",
            "requerido",
            "configuracion",
            "orden",
            "col",
            "area",
            "valor_default",
            "placeholder",
            "ayuda",
        }

        for i, campo in enumerate(campos):
            cls._validate_exact_keys(campo, required, f"campos[{i}]", errors)

    # =========================
    # FIELDS SEMANTICS
    # =========================

    @classmethod
    def _validate_fields_semantics(cls, data, campos, errors):

        nombres = set()
        orden_area = set()

        for i, campo in enumerate(campos):
            path = f"campos[{i}]"

            # nombre único
            nombre = campo.get("nombre")
            if nombre in nombres:
                errors.append({
                    "tipoError": "Nombre duplicado",
                    "ubicacion": f"{path}.nombre",
                    "elemento": nombre,
                    "sugerenciaCorreccion": "Cada campo debe tener un nombre único"
                })
            nombres.add(nombre)

            # tipo_base válido
            if campo.get("tipo_base") not in SQL_TYPES_KEYS:
                errors.append({
                    "tipoError": "tipo_base inválido",
                    "ubicacion": f"{path}.tipo_base",
                    "elemento": campo.get("tipo_base"),
                    "sugerenciaCorreccion": "Utiliza uno de los tipo_base permitidos"
                })

            # tipo_funcional válido
            if campo.get("tipo_funcional") not in CECOD_TYPES:
                errors.append({
                    "tipoError": "tipo_funcional inválido",
                    "ubicacion": f"{path}.tipo_funcional",
                    "elemento": campo.get("tipo_funcional"),
                    "sugerenciaCorreccion": "Utiliza uno de los tipo_funcional permitidos"
                })

            # orden único por área
            key = (campo.get("area"), campo.get("orden"))
            if key in orden_area:
                errors.append({
                    "tipoError": "Orden duplicado",
                    "ubicacion": f"{path}.orden",
                    "elemento": campo.get("orden"),
                    "sugerenciaCorreccion": "Cambia el orden en los campos que tienen valores duplicados perteneciendo a la misma área"
                })
            orden_area.add(key)

            # regla especial detalle: solo main
            if data.get("rol") == "detalle":
                if campo.get("area") != "main":
                    errors.append({
                        "tipoError": "Área inválida",
                        "ubicacion": f"{path}.area",
                        "elemento": campo.get("area"),
                        "sugerenciaCorreccion": "En modelos detalle solo se permite area 'main'"
                    })

    # =========================
    # CONFIG VALIDATION
    # =========================

    @classmethod
    def _validate_field_configurations(cls, campos, errors):

        for i, campo in enumerate(campos):
            tipo = campo.get("tipo_funcional")
            config = campo.get("configuracion", {})
            path = f"campos[{i}].configuracion"

            expected_keys = CECOD_CONFIG_STRUCTURE.get(tipo)

            if expected_keys is not None:
                cls._validate_exact_keys(config, expected_keys, path, errors)

    # =========================
    # UTIL
    # =========================

    @staticmethod
    def _validate_exact_keys(data, required_keys, path, errors):

        if not isinstance(data, dict):
            errors.append({
                "tipoError": "Tipo inválido",
                "ubicacion": path,
                "elemento": data,
                "sugerenciaCorreccion": "Debe ser un objeto"
            })
            return

        keys = set(data.keys())

        missing = required_keys - keys
        extra = keys - required_keys

        for m in missing:
            errors.append({
                "tipoError": "Campo requerido faltante",
                "ubicacion": f"{path}.{m}" if path else m,
                "elemento": None,
                "sugerenciaCorreccion": f"Agrega el campo requerido: {m}"
            })

        for e in extra:
            errors.append({
                "tipoError": "Campo no permitido",
                "ubicacion": f"{path}.{e}" if path else e,
                "elemento": data.get(e),
                "sugerenciaCorreccion": f"Elimina el campo no permitido: {e}"
            })