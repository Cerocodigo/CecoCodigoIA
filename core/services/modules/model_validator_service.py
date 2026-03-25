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
        print("Validando modelo...")
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
                "path": "",
                "message": "JSON inválido"
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
                    "path": key,
                    "message": "Debe ser slug válido (minúsculas, números y _)"
                })

        campos = data.get("campos", [])
        nombres = [c.get("nombre") for c in campos]

        # PK obligatorio
        if data.get("pk") not in nombres:
            errors.append({
                "path": "pk",
                "message": "El pk debe existir en los campos"
            })

        # FK obligatorio en detalle
        if data.get("rol") == "detalle":
            if data.get("fk") not in nombres:
                errors.append({
                    "path": "fk",
                    "message": "El fk debe existir en los campos del modelo detalle"
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
                    "path": f"{path}.nombre",
                    "message": "Nombre duplicado"
                })
            nombres.add(nombre)

            # tipo_base válido
            if campo.get("tipo_base") not in SQL_TYPES_KEYS:
                errors.append({
                    "path": f"{path}.tipo_base",
                    "message": "tipo_base inválido"
                })

            # tipo_funcional válido
            if campo.get("tipo_funcional") not in CECOD_TYPES:
                errors.append({
                    "path": f"{path}.tipo_funcional",
                    "message": "tipo_funcional inválido"
                })

            # orden único por área
            key = (campo.get("area"), campo.get("orden"))
            if key in orden_area:
                errors.append({
                    "path": f"{path}.orden",
                    "message": "Orden duplicado en la misma área"
                })
            orden_area.add(key)

            # regla especial detalle: solo main
            if data.get("rol") == "detalle":
                if campo.get("area") != "main":
                    errors.append({
                        "path": f"{path}.area",
                        "message": "En modelos detalle solo se permite area 'main'"
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
                "path": path,
                "message": "Debe ser un objeto"
            })
            return

        keys = set(data.keys())

        missing = required_keys - keys
        extra = keys - required_keys

        for m in missing:
            errors.append({
                "path": f"{path}.{m}" if path else m,
                "message": "Campo requerido faltante"
            })

        for e in extra:
            errors.append({
                "path": f"{path}.{e}" if path else e,
                "message": "Campo no permitido"
            })