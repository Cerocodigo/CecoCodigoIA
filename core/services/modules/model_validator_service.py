# core/services/modules/model_validator_service.py

import json
import re

from core.services.modules.constants import (
    MODEL_REQUIRED_FIELDS,
    FIELD_REQUIRED_FIELDS,
    SQL_TYPES_KEYS,
    CECOD_TYPES,
    CECOD_CONFIG_META,
    SQL_TYPE_META,
    TIPO_FUNCIONAL_META
)


class ModelValidatorService:
    """
    Servicio encargado de VALIDAR un modelo dinámico.

    IMPORTANTE:
    - Este servicio NO corrige, solo valida.
    - Se usa antes y después del proceso de corrección.
    - Detecta inconsistencias estructurales, semánticas y de configuración.

    Flujo:
        validate()
            ├── JSON válido
            ├── metadata (estructura + semántica)
            ├── campos (estructura + semántica)
            └── configuración por tipo funcional
    """

    # =========================
    # ENTRYPOINT
    # =========================

    @classmethod
    def validate(cls, model_json):
        """Valida un modelo dinámico a partir de su JSON o dict."""
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
        """Construye la respuesta estándar del validador."""
        return {
            "is_valid": len(errors) == 0,
            "errors": errors
        }

    # =========================
    # JSON VALIDATION
    # =========================

    @staticmethod
    def _validate_json(model_json, errors):
        """
        Valida que el input sea JSON válido o dict.

        Si es string → intenta parsear.
        Si falla → error crítico.
        """

        if isinstance(model_json, dict):
            return model_json

        try:
            return json.loads(model_json)
        except Exception:
            errors.append({
                "tipoError": "JSON inválido",
                "ubicacion": "modelo completo",
                "elemento": "JSON inválido",
                "sugerenciaCorreccion": "El JSON no es parseable"
            })
            return None

    # =========================
    # METADATA STRUCTURE
    # =========================

    @classmethod
    def _validate_metadata_structure(cls, data, errors):
        """
        Valida que la metadata tenga EXACTAMENTE los campos requeridos.

        ✔ Detecta:
            - faltantes
            - sobrantes
        """

        required = set(MODEL_REQUIRED_FIELDS["base"])

        if data.get("rol") == "detalle":
            required |= MODEL_REQUIRED_FIELDS["detalle_extra"]

        cls._validate_exact_keys(data, required, "", errors)

    # =========================
    # METADATA SEMANTICS
    # =========================

    @classmethod
    def _validate_metadata_semantics(cls, data, errors):
        """
        Valida coherencia lógica de metadata.

        ✔ Slugs válidos
        ✔ PK existente
        ✔ FK (si aplica)
        """

        # Validación de slug (_id y tabla)
        for key in ["_id", "tabla"]:
            val = data.get(key)
            if val and not re.match(r"^[a-z0-9_]+$", val):
                errors.append({
                    "tipoError": "Slug inválido",
                    "ubicacion": key,
                    "elemento": val,
                    "sugerenciaCorreccion": "Debe ser minúsculas, sin espacios"
                })

        campos = data.get("campos", [])
        nombres = [c.get("nombre") for c in campos]

        # PK debe existir como campo
        if data.get("pk") not in nombres:
            errors.append({
                "tipoError": "PK inválido",
                "ubicacion": "pk",
                "elemento": data.get("pk"),
                "sugerenciaCorreccion": "Debe existir en campos"
            })

        # FK solo en detalle
        if data.get("rol") == "detalle":
            if data.get("fk") not in nombres:
                errors.append({
                    "tipoError": "FK inválido",
                    "ubicacion": "fk",
                    "elemento": data.get("fk"),
                    "sugerenciaCorreccion": "Debe existir en campos"
                })

    # =========================
    # FIELDS STRUCTURE
    # =========================

    @classmethod
    def _validate_fields_structure(cls, campos, errors):
<<<<<<< mejoraValidadorJsonModelos
        """
        Valida estructura exacta de cada campo.
        """
=======

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
            "gap",
            "gap_top",
            "break",
        }
>>>>>>> main


        for i, campo in enumerate(campos):
            cls._validate_exact_keys(campo, FIELD_REQUIRED_FIELDS, f"campos[{i}]", errors)

    # =========================
    # FIELDS SEMANTICS
    # =========================

    @classmethod
    def _validate_fields_semantics(cls, data, campos, errors):
        """
        Valida coherencia interna de campos.

        ✔ nombre único
        ✔ tipo_base válido
        ✔ tipo_funcional válido
        ✔ consistencia entre ambos
        ✔ valor_default compatible
        ✔ orden por área sin duplicados
        """

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
                    "sugerenciaCorreccion": "Debe ser único"
                })
            nombres.add(nombre)

            tipo_base = campo.get("tipo_base")
            tipo_funcional = campo.get("tipo_funcional")

            # tipo_base válido
            if tipo_base not in SQL_TYPES_KEYS:
                errors.append({
                    "tipoError": "tipo_base inválido",
                    "ubicacion": f"{path}.tipo_base",
                    "elemento": tipo_base,
                    "sugerenciaCorreccion": "No permitido"
                })

            # tipo_funcional válido
            if tipo_funcional not in CECOD_TYPES:
                errors.append({
                    "tipoError": "tipo_funcional inválido",
                    "ubicacion": f"{path}.tipo_funcional",
                    "elemento": tipo_funcional,
                    "sugerenciaCorreccion": "No permitido"
                })

            # consistencia base vs funcional
            meta = TIPO_FUNCIONAL_META.get(tipo_funcional)
            if meta and tipo_base not in meta["bases_validas"]:
                errors.append({
                    "tipoError": "tipo_base inconsistente",
                    "ubicacion": f"{path}.tipo_base",
                    "elemento": tipo_base,
                    "sugerenciaCorreccion": f"Debe ser {meta['bases_validas']}"
                })

            # validación de valor_default
            result = cls.normalize_and_validate(
                campo.get("valor_default"),
                tipo_base
            )

            if not result["is_valid"]:
                errors.append({
                    "tipoError": "valor_default inválido",
                    "ubicacion": f"{path}.valor_default",
                    "elemento": campo.get("valor_default"),
                    "sugerenciaCorreccion": result["error"]
                })

            # orden único por área
            key = (campo.get("area"), campo.get("orden"))
            if key in orden_area:
                errors.append({
                    "tipoError": "Orden duplicado",
                    "ubicacion": f"{path}.orden",
                    "elemento": campo.get("orden"),
                    "sugerenciaCorreccion": "Duplicado en área"
                })
            orden_area.add(key)

<<<<<<< mejoraValidadorJsonModelos
            # validación especial para modelos tipo detalle
            if data.get("rol") == "detalle":
                if campo.get("area") != "main":
                    errors.append({
                        "tipoError": "Área inválida",
                        "ubicacion": f"{path}.area",
                        "elemento": campo.get("area"),
                        "sugerenciaCorreccion": "Solo 'main' permitido"
                    })
=======
            # regla especial detalle: solo main.. es indiferente el area en detalle
            # if data.get("rol") == "detalle":
            #     if campo.get("area") != "main":
            #         errors.append({
            #             "tipoError": "Área inválida",
            #             "ubicacion": f"{path}.area",
            #             "elemento": campo.get("area"),
            #             "sugerenciaCorreccion": "En modelos detalle solo se permite area 'main'"
            #         })
>>>>>>> main

    # =========================
    # CONFIG
    # =========================

    @classmethod
    def _validate_field_configurations(cls, campos, errors):
        """
        Valida estructura de configuraciones usando CECOD_CONFIG_META.
        """

        for i, campo in enumerate(campos):
            tipo = campo.get("tipo_funcional")

            meta = CECOD_CONFIG_META.get(tipo)
            if not meta:
                continue

            expected = meta["structure"]

            cls._validate_exact_keys(
                campo.get("configuracion", {}),
                expected,
                f"campos[{i}].configuracion",
                errors
            )

    # =========================
    # CORE SHARED LOGIC
    # =========================

    @staticmethod
    def normalize_and_validate(valor, tipo_base):
        """
        Intenta castear valor_default al tipo_base esperado.

        ✔ Corrige implícitamente
        ✔ Retorna si es válido o no
        """

        meta = SQL_TYPE_META.get(tipo_base)

        if not meta:
            return {"value": valor, "is_valid": False, "was_changed": False, "error": "tipo_base sin metadata"}

        default = meta["default"]
        caster = meta["cast"]

        if valor is None:
            return {"value": default, "is_valid": False, "was_changed": True, "error": "No puede ser null"}

        try:
            nuevo = caster(valor)
            return {"value": nuevo, "is_valid": True, "was_changed": nuevo != valor, "error": None}
        except Exception:
            return {"value": default, "is_valid": False, "was_changed": True, "error": "Tipo inválido"}

    # =========================
    # UTIL
    # =========================

    @staticmethod
    def _validate_exact_keys(data, required_keys, path, errors):
        """
        Valida que un dict tenga EXACTAMENTE las keys esperadas.

        ✔ Detecta faltantes
        ✔ Detecta extras
        """

        if not isinstance(data, dict):
            errors.append({
                "tipoError": "Tipo inválido",
                "ubicacion": path,
                "elemento": data,
                "sugerenciaCorreccion": "Debe ser objeto"
            })
            return

        keys = set(data.keys())

        for m in required_keys - keys:
            errors.append({
                "tipoError": "Campo requerido faltante",
                "ubicacion": f"{path}.{m}" if path else m,
                "elemento": None,
                "sugerenciaCorreccion": f"Agregar {m}"
            })

        for e in keys - required_keys:
            errors.append({
                "tipoError": "Campo no permitido",
                "ubicacion": f"{path}.{e}" if path else e,
                "elemento": data.get(e),
                "sugerenciaCorreccion": f"Eliminar {e}"
            })