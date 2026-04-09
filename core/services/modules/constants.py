# core/services/modules/constants.py
# ==================================================
# Constantes compartidas para módulos dinámicos
# ==================================================

# =========================
<<<<<<< mejoraValidadorJsonModelos
# Validación de estructura general de metadata en modelos
# =========================
MODEL_REQUIRED_FIELDS = {
    "base": {
        "_id",
        "activo",
        "tabla",
        "display",
        "rol",
        "pk",
        "campos",
        "modulo",
    },
    "detalle_extra": {
        "fk",
        "descripcion",
    }
}

# =========================
# Validación de estructura general de campos en modelos
# =========================
FIELD_REQUIRED_FIELDS = {
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



# =========================
# Valores por defecto para campos faltantes en metadata de modelo
# =========================
MODEL_DEFAULTS = {
    "activo": True,
    "rol": "cabecera",
    "campos": [],
}

# =========================
# Valores por defecto para campos faltantes en metadata de campo
# =========================
FIELD_DEFAULTS = {
    "visible": True,
    "requerido": False,
    "configuracion": {},
    "col": 6,
    "area": "main",
    "valor_default": None,
    "placeholder": "",
    "ayuda": "",
}



# =========================
# Definición de tipos funcionales y sus bases válidas (para validación y autocorrección)
# Tipo funcional → tipos base válidos y base default para autocorrección
# =========================
TIPO_FUNCIONAL_META = {
    "TextoSimple": {
        "bases_validas": {"string", "char", "text"},
        "base_default": "string",
    },
    "NumeroSimple": {
        "bases_validas": {"int", "integer", "decimal2", "decimal4", "decimal6"},
        "base_default": "decimal2",
    },
    "NumeroSecuencial": {
        "bases_validas": {"int", "integer", "pk", "fk"},
        "base_default": "int",
    },
    "SistemaFecha": {
        "bases_validas": {"date", "datetime"},
        "base_default": "datetime",
    },
    "SistemaUsuario": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "OpcionMultiple": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "Referencia": {
        "bases_validas": {"fk"},
        "base_default": "fk",
    },
    "ReferenciaBuscador": {
        "bases_validas": {"fk"},
        "base_default": "fk",
    },
    "ReferenciaAdjunto": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "QueryBaseDatos": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "Operacion": {
        "bases_validas": {"decimal2", "decimal4", "decimal6"},
        "base_default": "decimal2",
    },
    "FormatoTexto": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "Condicional": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "Archivo": {
        "bases_validas": {"string"},
        "base_default": "string",
    },
    "FormulaDetalle": {
        "bases_validas": {"decimal2", "decimal4", "decimal6","int", "integer"},
        "base_default": "decimal2",
    },
    
}

# =========================
# Para validación rápida de tipos funcionales en campos
# =========================
CECOD_TYPES = set(TIPO_FUNCIONAL_META.keys())


# =========================
# Definición de tipos base y su metadata asociada (para validación, autocorrección y generación de SQL)
# Tipo base → info de tipo SQL, valor default para autocorrección y función de casteo
# =========================

SQL_TYPE_META = {
    "pk": {
        "default": 0,
        "cast": int,
        "sql": "INT AUTO_INCREMENT PRIMARY KEY",
    },

    "string": {
        "default": "",
        "cast": str,
        "sql": "VARCHAR(255)",
    },
    "char": {
        "default": "",
        "cast": str,
        "sql": "CHAR(1)",
    },
    "text": {
        "default": "",
        "cast": str,
        "sql": "TEXT",
    },

    "int": {
        "default": 0,
        "cast": int,
        "sql": "INT",
    },
    "integer": {
        "default": 0,
        "cast": int,
        "sql": "INT",
    },

    "decimal2": {
        "default": 0.00,
        "cast": float,
        "sql": "DECIMAL(10,2)",
    },
    "decimal4": {
        "default": 0.0000,
        "cast": float,
        "sql": "DECIMAL(10,4)",
    },
    "decimal6": {
        "default": 0.000000,
        "cast": float,
        "sql": "DECIMAL(10,6)",
    },

    "boolean": {
        "default": 0,
        "cast": int,
        "sql": "TINYINT(1)",
    },

    "date": {
        "default": "1970-01-01",
        "cast": str,
        "sql": "DATE",
    },
    "datetime": {
        "default": "1970-01-01 00:00:00",
        "cast": str,
        "sql": "DATETIME",
    },
    "time": {
        "default": "00:00:00",
        "cast": str,
        "sql": "TIME",
    },

    "fk": {
        "default": 0,
        "cast": int,
        "sql": "INT",
    },
=======
# SQL TYPES (Mongo → MySQL)
# =========================
SQL_TYPES_MAP = {
    "pk": "INT AUTO_INCREMENT PRIMARY KEY",
    "string": "VARCHAR(255)",
    "char": "CHAR(1)",
    "text": "TEXT",
    "int": "INT",
    "integer": "INT",
    "decimal": "DECIMAL(10,2)",
    "decimal2": "DECIMAL(10,2)",
    "decimal4": "DECIMAL(10,4)",
    "decimal6": "DECIMAL(10,6)",
    "boolean": "TINYINT(1)",
    "date": "DATE",
    "datetime": "DATETIME",
    "time": "TIME",
    "fk": "INT",
}

# Solo las keys (para validación)
SQL_TYPES_KEYS = set(SQL_TYPES_MAP.keys())


# =========================
# TIPOS FUNCIONALES
# =========================
CECOD_TYPES = {
    "TextoSimple",
    "NumeroSimple",
    "NumeroSecuencial",
    "SistemaFecha",
    "SistemaUsuario",
    "OpcionMultiple",
    "Referencia",
    "ReferenciaBuscador",
    "ReferenciaAdjunto",
    "QueryBaseDatos",
    "Operacion",
    "FormatoTexto",
    "Condicional",
    "Archivo",
    "FormulaDetalle",
    "FechaRegistro",
    "LlaveExterna"
>>>>>>> main
}
# =========================
# Para validación rápida de tipos base en campos
# =========================
SQL_TYPES_KEYS = set(SQL_TYPE_META.keys())



# =========================
# Configuración de campos según tipo funcional (estructura esperada y valores por defecto para config faltante)
# NOTA: "defaults": None → no es autocorregible, requiere intervención manual
# =========================
<<<<<<< mejoraValidadorJsonModelos
CECOD_CONFIG_META = {
    "TextoSimple": {
        "structure": {"unico", "editable", "valor_predeterminado"},
        "defaults": {
            "unico": "No",
            "editable": "Si",
            "valor_predeterminado": "",
        },
    },

    "NumeroSimple": {
        "structure": {"min", "max"},
        "defaults": {
            "min": 0,
            "max": 999999,
        },
    },

    "NumeroSecuencial": {
        "structure": {"inicio", "incremento"},
        "defaults": {
            "inicio": 1,
            "incremento": 1,
        },
    },

    "SistemaFecha": {
        "structure": set(),
        "defaults": {},  # ✔ válido: config vacía
    },

    "SistemaUsuario": {
        "structure": {"modo"},
        "defaults": {
            "modo": "Usuario Actual",
        },
    },

    "OpcionMultiple": {
        "structure": {"opciones", "labels", "valor_predeterminado"},
        "defaults": {
            "opciones": [],
            "labels": {},
            "valor_predeterminado": None,
        },
    },

    "Referencia": {
        "structure": {
            "sql",
            "label_field",
            "value_field",
            "campo_principal",
            "campos_filtrables",
            "valor_inicial",
        },
        "defaults": None,
=======
CECOD_CONFIG_STRUCTURE = {
    "TextoSimple": {"unico", "editable", "valor_predeterminado"},
    "NumeroSimple": {"min", "max"},
    "NumeroSecuencial": {"inicio", "incremento"},
    "SistemaFecha": None,
    "SistemaUsuario": {"modo"},
    "OpcionMultiple": {"opciones", "labels", "valor_predeterminado"},
    "Referencia": {
        "sql",
        "label_field",
        "value_field",
        "campo_principal",
        #"campos_filtrables",
        "valor_inicial",
>>>>>>> main
    },

    "ReferenciaBuscador": {
<<<<<<< mejoraValidadorJsonModelos
        "structure": {
            "sql",
            "value_field",
            "label_field",
            "campos_filtrables",
        },
        "defaults": None,
    },

    "ReferenciaAdjunto": {
        "structure": {"referencia", "campo_origen", "editable"},
        "defaults": None,
    },

    "QueryBaseDatos": {
        "structure": {"query", "parametros"},
        "defaults": None,
    },

    "Operacion": {
        "structure": {"formula"},
        "defaults": None,
    },

    "FormatoTexto": {
        "structure": {"template", "padding"},
        "defaults": None,
    },

    "Condicional": {
        "structure": {"condicional"},
        "defaults": None,
    },

    "Archivo": {
        "structure": {"acepta_archivo", "tamano_max_mb"},
        "defaults": {
            "acepta_archivo": "cualquiera",
            "tamano_max_mb": 10,
        },
    },

    "FormulaDetalle": {
        "structure": {"operacion", "campo", "tabla", "condicion"},
        "defaults": None,
    },
=======
        "sql",
        "value_field",
        "label_field",
        "campos_filtrables",
        "campo_principal",
        "valor_inicial",
        "ModuloIngresoRapido",

    },
    "ReferenciaAdjunto": {"referencia", "campo_origen", "editable"},
    "QueryBaseDatos": {"query", "parametros"},
    "Operacion": {"formula"},
    "FormatoTexto": {"template", "padding"},
    "Condicional": {"condicional"},
    "Archivo": {"acepta_archivo", "tamano_max_mb"},
    "FormulaDetalle": {"operacion", "campo", "tabla", "condicion"},
    "FechaRegistro": {"editable"},
    "LlaveExterna": {"entidad", "campo"},
    
    
>>>>>>> main
}