# core/services/plantillas_prehecho/metadata_validation_service.py

import re

from django.core.exceptions import ValidationError


class MetadataValidationService:
    """
    Servicio encargado de validar la estructura
    de data_variables_mongo definida en:

    ModeloPrehechoEjecutar.data_variables_mongo
    """

    # =========================
    # Tipos válidos
    # =========================
    VALID_TYPES = [
        "texto",
        "textarea",
        "email",
        "numero",
        "decimal",
        "fecha",
        "imagen",
        "p12",
        "select",
    ]

    # =========================
    # Campos requeridos
    # =========================
    REQUIRED_FIELDS = [
        "variable",
        "label",
        "tipo",
        "metadata",
    ]

    # =========================
    # Campos requeridos metadata
    # =========================
    METADATA_REQUIRED_FIELDS = [
        "tipo",
        "coleccion_aplicar",
        "condicion_aplicar",
        "campo_aplicar",
        "elemento_aplicar",
    ]

    # =========================
    # Validaciones soportadas
    # =========================
    VALIDATION_RULES = {
        "texto": [
            "min_length",
            "max_length",
            "regex",
        ],

        "textarea": [
            "min_length",
            "max_length",
            "regex",
        ],

        "email": [
            "min_length",
            "max_length",
            "regex",
        ],

        "numero": [
            "min",
            "max",
        ],

        "decimal": [
            "min",
            "max",
        ],

        "fecha": [
            "min",
            "max",
        ],

        "imagen": [
            "extensiones",
            "max_size_mb",
        ],

        "p12": [
            "extensiones",
            "max_size_mb",
        ],

        "select": [
            "options",
        ],
    }

    # =========================
    # Validar estructura completa
    # =========================
    @staticmethod
    def validate_structure(data_variables_mongo):
        """
        Valida estructura completa de metadata dinámica.
        """

        # =========================
        # None permitido
        # =========================
        if data_variables_mongo is None:
            return True

        # =========================
        # Debe ser array
        # =========================
        if not isinstance(data_variables_mongo, list):
            raise ValidationError(
                "data_variables_mongo debe ser una lista"
            )

        # =========================
        # Recorrer elementos
        # =========================
        for index, item in enumerate(data_variables_mongo):

            MetadataValidationService.validate_item(
                item=item,
                index=index,
            )

        return True

    # =========================
    # Validar item individual
    # =========================
    @staticmethod
    def validate_item(item, index=0):
        """
        Valida un item individual del array.
        """

        # =========================
        # Tipo dict obligatorio
        # =========================
        if not isinstance(item, dict):
            raise ValidationError(
                f"Item #{index} debe ser un objeto JSON"
            )

        # =========================
        # Campos requeridos
        # =========================
        for field in MetadataValidationService.REQUIRED_FIELDS:

            if field not in item:
                raise ValidationError(
                    f"Campo requerido faltante: {field}"
                )

        # =========================
        # variable
        # =========================
        variable = item.get("variable", "")

        if not isinstance(variable, str):
            raise ValidationError(
                "variable debe ser string"
            )

        if not variable.strip():
            raise ValidationError(
                "variable no puede estar vacío"
            )

        # snake_case obligatorio
        if not re.match(r"^[a-z0-9_]+$", variable):
            raise ValidationError(
                "variable debe usar snake_case"
            )

        # =========================
        # label
        # =========================
        label = item.get("label", "")

        if not isinstance(label, str):
            raise ValidationError(
                "label debe ser string"
            )

        if not label.strip():
            raise ValidationError(
                "label no puede estar vacío"
            )

        # =========================
        # tipo
        # =========================
        tipo = item.get("tipo")

        if tipo not in MetadataValidationService.VALID_TYPES:
            raise ValidationError(
                f"Tipo inválido: {tipo}"
            )

        # =========================
        # help_text opcional
        # =========================
        help_text = item.get("help_text")

        if help_text is not None:
            if not isinstance(help_text, str):
                raise ValidationError(
                    "help_text debe ser string"
                )

        # =========================
        # validaciones opcional
        # =========================
        validaciones = item.get("validaciones")

        if validaciones is not None:

            MetadataValidationService.validate_validaciones(
                tipo=tipo,
                validaciones=validaciones,
            )

        # =========================
        # directorio opcional
        # =========================
        directorio = item.get("directorio")

        if directorio is not None:

            if not isinstance(directorio, str):
                raise ValidationError(
                    "directorio debe ser string"
                )

            if not directorio.strip():
                raise ValidationError(
                    "directorio no puede estar vacío"
                )

            if not re.match(r"^[a-zA-Z0-9_\-]+$", directorio):
                raise ValidationError(
                    "directorio contiene caracteres inválidos"
                )

        # =========================
        # metadata obligatorio
        # =========================
        metadata = item.get("metadata")

        MetadataValidationService.validate_metadata(
            metadata=metadata
        )

    # =========================
    # Validar metadata
    # =========================
    @staticmethod
    def validate_metadata(metadata):
        """
        Valida bloque metadata.
        """

        if not isinstance(metadata, dict):
            raise ValidationError(
                "metadata debe ser un objeto"
            )

        # =========================
        # Campos requeridos
        # =========================
        for field in MetadataValidationService.METADATA_REQUIRED_FIELDS:

            if field not in metadata:
                raise ValidationError(
                    f"metadata.{field} es requerido"
                )

        # =========================
        # tipo
        # =========================
        metadata_tipo = metadata.get("tipo")

        if not isinstance(metadata_tipo, str):
            raise ValidationError(
                "metadata.tipo debe ser string"
            )

        if not metadata_tipo.strip():
            raise ValidationError(
                "metadata.tipo no puede estar vacío"
            )

        # =========================
        # coleccion_aplicar
        # =========================
        coleccion_aplicar = metadata.get(
            "coleccion_aplicar"
        )

        if not isinstance(coleccion_aplicar, str):
            raise ValidationError(
                "metadata.coleccion_aplicar debe ser string"
            )

        if not coleccion_aplicar.strip():
            raise ValidationError(
                "metadata.coleccion_aplicar no puede estar vacío"
            )

        # =========================
        # condicion_aplicar
        # =========================
        condicion_aplicar = metadata.get(
            "condicion_aplicar"
        )

        if not isinstance(condicion_aplicar, dict):
            raise ValidationError(
                "metadata.condicion_aplicar debe ser dict"
            )

        # =========================
        # campo_aplicar
        # =========================
        campo_aplicar = metadata.get(
            "campo_aplicar"
        )

        if not isinstance(campo_aplicar, str):
            raise ValidationError(
                "metadata.campo_aplicar debe ser string"
            )

        # Puede venir vacío
        # "" o "*" = aplicar globalmente

        # =========================
        # elemento_aplicar
        # =========================
        elemento_aplicar = metadata.get(
            "elemento_aplicar"
        )

        if not isinstance(elemento_aplicar, str):
            raise ValidationError(
                "metadata.elemento_aplicar debe ser string"
            )

        # Puede venir vacío

    # =========================
    # Validar reglas validaciones
    # =========================
    @staticmethod
    def validate_validaciones(
        tipo,
        validaciones,
    ):
        """
        Valida reglas definidas dentro
        de "validaciones".
        """

        if not isinstance(validaciones, dict):
            raise ValidationError(
                "validaciones debe ser dict"
            )

        allowed_rules = (
            MetadataValidationService.VALIDATION_RULES.get(
                tipo,
                []
            )
        )

        # =========================
        # Validar claves soportadas
        # =========================
        for rule_name in validaciones.keys():

            if rule_name not in allowed_rules:
                raise ValidationError(
                    f"Regla inválida '{rule_name}' para tipo '{tipo}'"
                )

        # =========================
        # Validaciones específicas
        # =========================

        # min_length
        if "min_length" in validaciones:

            if not isinstance(
                validaciones["min_length"],
                int
            ):
                raise ValidationError(
                    "min_length debe ser int"
                )

        # max_length
        if "max_length" in validaciones:

            if not isinstance(
                validaciones["max_length"],
                int
            ):
                raise ValidationError(
                    "max_length debe ser int"
                )

        # regex
        if "regex" in validaciones:

            regex = validaciones["regex"]

            if not isinstance(regex, str):
                raise ValidationError(
                    "regex debe ser string"
                )

            try:
                re.compile(regex)
            except Exception:
                raise ValidationError(
                    "regex inválido"
                )

        # min
        if "min" in validaciones:

            if not isinstance(
                validaciones["min"],
                (int, float)
            ):
                raise ValidationError(
                    "min debe ser numérico"
                )

        # max
        if "max" in validaciones:

            if not isinstance(
                validaciones["max"],
                (int, float)
            ):
                raise ValidationError(
                    "max debe ser numérico"
                )

        # extensiones
        if "extensiones" in validaciones:

            extensiones = validaciones["extensiones"]

            if not isinstance(extensiones, list):
                raise ValidationError(
                    "extensiones debe ser lista"
                )

            for ext in extensiones:

                if not isinstance(ext, str):
                    raise ValidationError(
                        "Cada extensión debe ser string"
                    )

                if not ext.startswith("."):
                    raise ValidationError(
                        "Las extensiones deben iniciar con punto"
                    )

        # max_size_mb
        if "max_size_mb" in validaciones:

            if not isinstance(
                validaciones["max_size_mb"],
                (int, float)
            ):
                raise ValidationError(
                    "max_size_mb debe ser numérico"
                )

        # options
        if "options" in validaciones:

            options = validaciones["options"]

            if not isinstance(options, list):
                raise ValidationError(
                    "options debe ser lista"
                )

            for option in options:

                if not isinstance(option, dict):
                    raise ValidationError(
                        "Cada option debe ser objeto"
                    )

                if "value" not in option:
                    raise ValidationError(
                        "option.value es requerido"
                    )

                if "label" not in option:
                    raise ValidationError(
                        "option.label es requerido"
                    )

        return True